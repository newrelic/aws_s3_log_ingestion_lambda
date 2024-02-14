import json
import sys
import urllib.parse
import boto3
import gzip
import os
from urllib import request
import aiohttp
import asyncio
import time
import logging
from smart_open import open
import re
from dateutil import parser


logger = logging.getLogger()

US_LOGGING_INGEST_HOST = "https://log-api.newrelic.com/log/v1"
EU_LOGGING_INGEST_HOST = 'https://log-api.eu.newrelic.com/log/v1'
LOGGING_LAMBDA_VERSION = '1.2.0'
LOGGING_PLUGIN_METADATA = {
    'type': "s3-lambda",
    'version': LOGGING_LAMBDA_VERSION
}


class InvalidArgumentException(Exception):
    pass


def _format_error(e, text):
    return "{}. {}".format(e, text)

def _get_optional_env(key, default):
    """
    Returns the default value even if the environment variable is set but empty
    """
    return os.getenv(key, default) or default

def _get_additional_attributes(attributes=None):
    """
    This function gets Environment variable 'ADDITIONAL_ATTRIBUTES' and parses the  same as a json object. Defaults
    to an empty map.
    :param `additional_attributes` : Returns the parameter value if present
    :raises
        InvalidArgumentException : If the os environment variable 'ADDITIONAL_ATTRIBUTES' is not a valid json object or
        If the os environment variable 'ADDITIONAL_ATTRIBUTES' is not of type (str, bytes or bytearray).
    :return: Dict of attributes (key,value) to add to payload
    """
    if attributes:
        return attributes
    env_attributes = _get_optional_env("ADDITIONAL_ATTRIBUTES", "{}")
    try:
        return json.loads(env_attributes)
    except json.JSONDecodeError as e:
        raise InvalidArgumentException(_format_error(e, "Invalid Json object"))
    except TypeError as e:
        raise InvalidArgumentException(_format_error(e, "The type of object should be one of the following (str, "
                                                        "bytes or bytearray)"))


additional_attributes = _get_additional_attributes()
# Maximum number of retries
MAX_RETRIES = 5
# Initial backoff (in seconds) between retries
INITIAL_BACKOFF = 1
# Multiplier factor for the backoff between retries
BACKOFF_MULTIPLIER = 2
# Max length in bytes of an individual log line
MAX_INDIVIDUAL_LOG_SIZE = 250 * 1024
# Max file size in bytes (uncompressed)
MAX_FILE_SIZE = 400 * 1000 * 1024
# Max batch size for sending requests (1MB)
MAX_BATCH_SIZE = 1000 * 1024
BATCH_SIZE_FACTOR = 1.5

REQUEST_BATCH_SIZE = 25

completed_requests = 0


class MaxRetriesException(Exception):
    pass


class BadRequestException(Exception):
    pass


def _is_ignore_log_file(key=None, regex_pattern=None):
    """
    This functions checks whether this log file should be ignored based on regex pattern.
    """
    if not regex_pattern:
        regex_pattern = _get_optional_env("S3_IGNORE_PATTERN", "$^")

    return bool(re.search(regex_pattern, key))


def _isCloudTrail(key=None, regex_pattern=None):
    """
    This functions checks whether this log file is a CloudTrail log based on regex pattern.
    """
    if not regex_pattern:
        regex_pattern = _get_optional_env(
            "S3_CLOUD_TRAIL_LOG_PATTERN", ".*_CloudTrail_.*\.json.gz$")

    return bool(re.search(regex_pattern, key))

def _isCloudTrailDigest(key=None):
    """
    This functions checks whether this log file is a CloudTrail-Digest based on regex pattern.
    """
    return bool(re.search(".*_CloudTrail-Digest_.*\.json.gz$", key))

def _convert_float(s):
    try:
        f = float(s)
    except ValueError:
        f = 1.5
    return f

def _get_batch_size_factor(batch_size_factor=None):
    """
    This functions gets BATCH_SIZE_FACTOR from env vars.
    """
    if batch_size_factor:
        return batch_size_factor
    return _convert_float(_get_optional_env("BATCH_SIZE_FACTOR", BATCH_SIZE_FACTOR))

def _get_license_key(license_key=None):
    """
    This functions gets New Relic's license key from env vars.
    """
    if license_key:
        return license_key
    return _get_optional_env("LICENSE_KEY", "")


def _get_log_type(log_type=None):
    """
    This functions gets the New Relic logtype from env vars.
    """
    return log_type or _get_optional_env("LOG_TYPE", "")


def _setting_console_logging_level():
    """
    Determines whether or not debug logging should be enabled based on the env var.
    Defaults to false.
    """
    if _get_optional_env("DEBUG_ENABLED", "false").lower() == "true":
        print("enabling debug mode")
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)


def _get_logging_endpoint(ingest_url=None):
    """
    Service url is determined by the license key's region.
    Any other URL could be passed by using the NR_LOGGING_ENDPOINT env var.
    """
    if ingest_url:
        return ingest_url
    if "NR_LOGGING_ENDPOINT" in os.environ:
        return os.environ["NR_LOGGING_ENDPOINT"]
    return (
        EU_LOGGING_INGEST_HOST
        if _get_license_key().startswith("eu")
        else US_LOGGING_INGEST_HOST
    )


def _compress_payload(data):
    """
    Return a list of payloads to be sent to New Relic.
    This method usually returns a list of one element, but can be bigger if the
    payload size is too big
    """
    logger.debug(f"uncompressed size: {sys.getsizeof(json.dumps(data).encode())}")
    payload = gzip.compress(json.dumps(data).encode())
    logger.debug(f"compressed size: {sys.getsizeof(payload)}")
    return payload


def _package_log_payload(data):
    """
    Packages up a MELT request for log messages
    """
    logLines = data["entry"]
    log_messages = []

    log_type = _get_log_type()
    for line in logLines:
        if log_type == "cloudfront-web":
            timestamp_matches = re.match(r"^([\d-]+\s[\d:]+)", line)
            if timestamp_matches is not None:
                timestamp = time.mktime((parser.parse(timestamp_matches.group(0))).timetuple())
            else:
                timestamp = ""
            log_messages.append({'message': line, 'timestamp': timestamp })
        else:
            log_messages.append({'message': line})
    attributes = {
        "plugin": LOGGING_PLUGIN_METADATA,
        "aws": {
            "invoked_function_arn": data["context"]["invoked_function_arn"],
            "s3_bucket_name": data["context"]["s3_bucket_name"],
            "s3_key": data["context"]["s3_key"]},
        "logtype": log_type
    }
    packaged_payload = [
        {
            "common": {
                "attributes": {**attributes, **additional_attributes}
            },
            "logs": log_messages,
        }]
    return packaged_payload


def create_request(payload, ingest_url=None, license_key=None):
    req = request.Request(_get_logging_endpoint(ingest_url), payload)
    req.add_header("X-License-Key", _get_license_key(license_key))
    req.add_header("X-Event-Source", "logs")
    req.add_header("Content-Encoding", "gzip")
    return req


async def send_log(session, url, data, headers):
    global completed_requests
    backoff = INITIAL_BACKOFF
    retries = 0
    while retries < MAX_RETRIES:
        if retries > 0:
            logger.info("Retrying in {} seconds".format(backoff))
            await asyncio.sleep(backoff)
            backoff *= BACKOFF_MULTIPLIER

        retries += 1
        try:
            completed_requests = completed_requests + 1
            resp = await session.post(url, data=data, headers=headers)
            resp.raise_for_status()
            completed_requests -= 1
            logger.debug(f"requests remaining: {completed_requests}")
            return resp.status, resp.url
        except aiohttp.ClientResponseError as e:
            if e.status == 400:
                raise BadRequestException(
                    _format_error(e, "Unexpected payload"))
            elif e.status == 403:
                raise BadRequestException(
                    _format_error(e, "Review your license key"))
            elif e.status == 404:
                raise BadRequestException(
                    _format_error(e, "Review the region endpoint")
                )
            elif e.status == 429:
                logger.error(
                    f"There was a {e.status} error. Reason: {e.message}")
                # Now retry the request
                continue
            elif e.status == 408:
                logger.error(
                    f"There was a {e.status} error. Reason: {e.message}")
                # Now retry the request
                continue
            elif 400 <= e.status < 500:
                raise BadRequestException(e)

    raise MaxRetriesException()


def create_log_payload_request(data, session):
    payload = _package_log_payload(data)
    payload = _compress_payload(payload)
    req = create_request(payload)
    return send_log(session, req.get_full_url(), req.data, req.headers)


async def _fetch_data_from_s3(bucket, key, context):
    """
        Stream data from S3 bucket. Create batches of size MAX_PAYLOAD_SIZE
        and create async requests from batches
    """
    log_file_size = boto3.resource('s3').Bucket(
        bucket).Object(key).content_length
    if log_file_size > MAX_FILE_SIZE:
        logger.error(
            "The log file uploaded to S3 is larger than the supported max size of 400MB")
        return
    BATCH_SIZE_FACTOR = _get_batch_size_factor()
    s3MetaData = {
        "invoked_function_arn": context.invoked_function_arn,
        "s3_bucket_name": bucket,
        "s3_key": key
    }
    log_file_url = "s3://{}/{}".format(bucket, key)
    if _isCloudTrailDigest(key):
        # CloudTrail-Digest will not have any logs in it. Hence, no need to continue further
        return
    async with aiohttp.ClientSession() as session:
        log_batches = []
        batch_request = []
        batch_counter = 1
        log_batch_size = 0
        start = time.time()
        with open(log_file_url, encoding='utf-8') as log_lines:
            if _isCloudTrail(key):
                # This is a CloudTrail log - we need to apply special preprocessing
                cloudtrail_events=json.loads(log_lines.read())["Records"]
                for this_event in cloudtrail_events:
                    # Convert the eventTime to Posix time and pass it to New Relic as a timestamp attribute
                    this_event['timestamp']=time.mktime((parser.parse(this_event['eventTime'])).timetuple())
                log_lines = cloudtrail_events

            for index, log in enumerate(log_lines):
                log_batch_size += sys.getsizeof(str(log))
                if index % 500 == 0:
                    logger.debug(f"index: {index}")
                    logger.debug(f"log_batch_size: {log_batch_size}")
                log_batches.append(log)
                if log_batch_size > (MAX_BATCH_SIZE * BATCH_SIZE_FACTOR):
                    logger.debug(f"sending batch: {batch_counter} log_batch_size: {log_batch_size}")
                    data = {"context": s3MetaData, "entry": log_batches}
                    batch_request.append(create_log_payload_request(data, session))
                    if len(batch_request) >= REQUEST_BATCH_SIZE:
                        await asyncio.gather(*batch_request)
                        batch_request = []
                    log_batches = []
                    log_batch_size = 0
                    batch_counter += 1
        data = {"context": s3MetaData, "entry": log_batches}
        batch_request.append(create_log_payload_request(data, session))
        logger.info("Sending data to NR logs.....")
        output = await asyncio.gather(*batch_request)
        end = time.time()
        logger.debug(f"time elapsed to send to NR Logs: {end - start}")


####################
#  Lambda handler  #
####################

def lambda_handler(event, context):
    # Get bucket from s3 upload event
    _setting_console_logging_level()
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(
        event['Records'][0]['s3']['object']['key'], encoding='utf-8')

    # Allow user to skip log file using regex pattern set in env variable: S3_IGNORE_PATTERN 
    if _is_ignore_log_file(key):
        logger.debug(f"Ignore log file based on S3_IGNORE_PATTERN: {key}")
        return {'statusCode': 200, 'message': 'ignored this log'}

    try:
        asyncio.run(_fetch_data_from_s3(bucket, key, context))
    except KeyError as e:
        logger.error(e)
        logger.error(
            f'Error getting object {key} from bucket {bucket}. Make sure they exist and your bucket is in the same region as this function.')
        raise e
    except OSError as e:
        logger.error(e)
        logger.error(
            f"Error processing the object {key} from bucket {bucket}.")
        raise e
    except MaxRetriesException as e:
        logger.error("Retry limit reached. Failed to send log entry.")
        raise e
    except BadRequestException as e:
        logger.error(e)
        raise e
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        raise e
    else:
        return {'statusCode': 200, 'message': 'Uploaded logs to New Relic'}


if __name__ == "__main__":
    lambda_handler('', '')
