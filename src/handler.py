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
from pympler import asizeof
from dateutil import parser


logger = logging.getLogger()

US_LOGGING_INGEST_HOST = "https://log-api.newrelic.com/log/v1"
EU_LOGGING_INGEST_HOST = 'https://log-api.eu.newrelic.com/log/v1'
LOGGING_LAMBDA_VERSION = '1.1.2'
LOGGING_PLUGIN_METADATA = {
    'type': "s3-lambda",
    'version': LOGGING_LAMBDA_VERSION
}

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


def _get_license_key(license_key=None):
    """
    This functions gets New Relic's license key from env vars.
    """
    if license_key:
        return license_key
    return os.getenv("LICENSE_KEY", "")


def _get_log_type(log_type=None):
    """
    This functions gets the New Relic logtype from env vars.
    """
    return log_type or os.getenv("LOG_TYPE") or os.getenv("LOGTYPE", "")


def _setting_console_logging_level():
    """
    Determines whether or not debug logging should be enabled based on the env var.
    Defaults to false.
    """
    if os.getenv("DEBUG_ENABLED", "false").lower() == "true":
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
    payload = gzip.compress(json.dumps(data).encode())
    return payload


def _package_log_payload(data):
    """
    Packages up a MELT request for log messages
    """
    logLines = data["entry"]
    log_messages = []

    for line in logLines:
        log_messages.append({'message': line})
    packaged_payload = [
        {
            "common": {
                "attributes": {
                    "plugin": LOGGING_PLUGIN_METADATA,
                    "aws": {
                        "invoked_function_arn": data["context"]["invoked_function_arn"],
                        "s3_bucket_name": data["context"]["s3_bucket_name"]},
                    "logtype": _get_log_type()
                }},
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
    def _format_error(e, text):
        return "{}. {}".format(e, text)
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

    s3MetaData = {
        "invoked_function_arn": context.invoked_function_arn,
        "s3_bucket_name": bucket
    }
    log_file_url = "s3://{}/{}".format(bucket, key)
    async with aiohttp.ClientSession() as session:
        log_batches = []
        batch_request = []
        batch_counter = 1
        start = time.time()
        isCloudTrail = bool(re.search(".*CloudTrail.*\.json.gz$", key))
        with open(log_file_url, encoding='utf-8') as log_lines:
            for index, log in enumerate(log_lines):
                if isCloudTrail:
                    # This is a CloudTrail log - we need to apply special preprocessing
                    cloudtrail_events=json.loads(log)["Records"]
                    for this_event in cloudtrail_events:
                        # Convert the eventTime to Posix time and pass it to New Relic as a timestamp attribute
                        this_event['timestamp']=time.mktime((parser.parse(this_event['eventTime'])).timetuple())
                    log_batches.extend(cloudtrail_events)
                else:
                    if index % 500 == 0:
                        logger.debug(f"index: {index}")
                    log_batches.append(log)
                if asizeof.asizeof(log_batches) > (MAX_BATCH_SIZE * BATCH_SIZE_FACTOR):
                    logger.debug(f"sending batch: {batch_counter}")
                    data = {"context": s3MetaData, "entry": log_batches}
                    batch_request.append(create_log_payload_request(data, session))
                    if len(batch_request) >= REQUEST_BATCH_SIZE:
                        await asyncio.gather(*batch_request)
                        batch_request = []
                    log_batches = []
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
