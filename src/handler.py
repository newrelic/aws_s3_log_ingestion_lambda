import json
import urllib.parse
import boto3
import gzip
import os
import re
from urllib import request
import aiohttp
import asyncio
from smart_open import open
from pympler import asizeof
from hurry.filesize import size

from dotenv import load_dotenv
load_dotenv(verbose=True)


s3 = boto3.client('s3')

US_LOGGING_INGEST_HOST = "https://log-api.newrelic.com/log/v1"
EU_LOGGING_INGEST_HOST = 'https://log-api.eu.newrelic.com/log/v1'
LOGGING_LAMBDA_VERSION = '1.0.0'
LOGGING_PLUGIN_METADATA = {
    'type': 's3-lambda',
    'version': LOGGING_LAMBDA_VERSION
}

# Maximum number of retries
MAX_RETRIES = 3
# Initial backoff (in seconds) between retries
INITIAL_BACKOFF = 1
# Multiplier factor for the backoff between retries
BACKOFF_MULTIPLIER = 2
# Max length in bytes of the payload
MAX_PAYLOAD_SIZE = 1000 * 1024
# Max length in bytes of an individual log line
MAX_INDIVIDUAL_LOG_SIZE = 250 * 1024
# Max file size in bytes (uncompressed)
MAX_PAYLOAD_SIZE = 150 * 1000 * 1024
# Multiplier for calculating batch sizes
BATCH_SIZE_FACTOR = 1.5


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


def _debug_logging_enabled():
    """
    Determines whether or not debug logging should be enabled based on the env var.
    Defaults to false.
    """
    return os.getenv("DEBUG_ENABLED", "false").lower() == "true"


async def http_post(session, url, data, headers):
    def _format_error(e, text):
        return "{}. {}".format(e, text)

    backoff = INITIAL_BACKOFF
    retries = 0

    while retries < MAX_RETRIES:
        if retries > 0:
            print("Retrying in {} seconds".format(backoff))
            await asyncio.sleep(backoff)
            backoff *= BACKOFF_MULTIPLIER

        retries += 1

        try:
            resp = await session.post(url, data=data, headers=headers)
            resp.raise_for_status()
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
                print("There was a {} error. Reason: {}".format(
                    e.status, e.message))
                # Now retry the request
                continue
            elif 400 <= e.status < 500:
                raise BadRequestException(e)

    raise MaxRetriesException()

####################


def _get_logging_request_creator(payload, ingest_url=None, license_key=None):
    def create_request():
        req = request.Request(_get_logging_endpoint(ingest_url), payload)
        req.add_header("X-License-Key", _get_license_key(license_key))
        req.add_header("X-Event-Source", "logs")
        req.add_header("Content-Encoding", "gzip")
        return req

    return create_request


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


def _split_log_payload(payload):
    """
    When data size is bigger than supported payload, it is divided in two
    different requests
    """
    common = payload[0]["common"]
    logs = payload[0]["logs"]
    half = len(logs) // 2

    return [
        _reconstruct_log_payload(common, logs[:half]),
        _reconstruct_log_payload(common, logs[half:]),
    ]


def _reconstruct_log_payload(common, logs):
    return [{"common": common, "logs": logs}]


async def _send_payload(request_creator, session, retry=False):
    """
    Send log payload to New Relic Logging API
    """
    try:
        req = request_creator()
        status, url = await http_post(
            session, req.get_full_url(), req.data, req.headers
        )
    except MaxRetriesException as e:
        print("Retry limit reached. Failed to send log entry.")
        if retry:
            raise e
    except BadRequestException as e:
        print(e)
    else:
        print("Log entry sent. Response code: {}. url: {}".format(status, url))
        return status


def _generate_payloads(data, split_function):
    """
    Return a list of payloads to be sent to New Relic.
    This method usually returns a list of one element, but can be bigger if the
    payload size is too big
    """
    payload = gzip.compress(json.dumps(data).encode())

    if len(payload) < MAX_PAYLOAD_SIZE:
        return [payload]

    split_data = split_function(data)
    return _generate_payloads(split_data[0], split_function) + _generate_payloads(
        split_data[1], split_function
    )


async def _send_log_entry(logLines, context, bucket_name):
    """
    This function sends the log entry to New Relic Logging's ingest
    server. If it is necessary, entries will be split in different payloads
    """
    s3MetaData = {
        "function_name": context.function_name,
        "invoked_function_arn": context.invoked_function_arn,
        "log_group_name": context.log_group_name,
        "log_stream_name": context.log_stream_name,
        "s3_bucket_name": bucket_name
    }

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=3)) as session:
        requests = []
        data = {"context": s3MetaData, "entry": logLines}

        payload_data = _generate_payloads(
            _package_log_payload(data), _split_log_payload)
        for payload in payload_data:
            requests.append(_send_payload(
                _get_logging_request_creator(payload), session))

        return await asyncio.gather(*requests)


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
                        "function_name": data["context"]["function_name"],
                        "invoked_function_arn":data["context"]["invoked_function_arn"],
                        "log_group_name": data["context"]["log_group_name"],
                        "log_stream_name": data["context"]["log_stream_name"],
                        "s3_bucket_name": data["context"]["s3_bucket_name"]},
                }},
            "logs": log_messages,
        }]
    return packaged_payload

    def _split_log_payload(payload):
        """
        When data size is bigger than supported payload, it is divided in two
        different requests
        """
        common = payload[0]["common"]
        logs = payload[0]["logs"]
        half = len(logs) // 2

        return [
            _reconstruct_log_payload(common, logs[:half]),
            _reconstruct_log_payload(common, logs[half:]),
        ]

def _fetch_data_from_s3(bucket, key, context):
    """
        Stream data from S3 bucket. Create batches of size MAX_PAYLOAD_SIZE*BATCH_SIZE_FACTOR
        and create async requests from batches
    """
    log_file_url = "s3://{}/{}".format(bucket, key)
    log_file_size = boto3.resource('s3').Bucket(bucket).Object(key).content_length
    if log_file_size > MAX_PAYLOAD_SIZE:
        print(f"The log file uploaded to S3 is larger than the supported max size of 150MB")
        return
    batch = []
    for line in open(log_file_url, encoding='utf-8'):
            if asizeof.asizeof(line) > MAX_INDIVIDUAL_LOG_SIZE:
                print(f"Log line of size {asizeof.asizeof(line)} is greater than the 0.25MB max log line size. This log will be dropped.")
                continue
            try:
                batch.append(json.loads(line))
            except json.JSONDecodeError:
                print(f"Log file is not in JSON format. Processing the log file as a string.")
                batch.append(line)
            if asizeof.asizeof(batch) > (MAX_PAYLOAD_SIZE*BATCH_SIZE_FACTOR):
                asyncio.run(_send_log_entry(batch, context, bucket))
                batch = []
    asyncio.run(_send_log_entry(batch, context, bucket))


####################
#  Lambda handler  #
####################


def lambda_handler(event, context):
    # Get bucket from s3 upload event
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(
        event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    try:
        _fetch_data_from_s3(bucket, key, context)
    except KeyError as e:
        print(e)
        print(
            'Error getting object {} from bucket {}. Make sure they exist and your bucket is in the same region as this function.'.format(
                key,
                bucket))
        raise e
    except OSError as e:
        print(e)
        print("Error processing the object {} from bucket {}.".format(key, bucket))
        raise e


if __name__ == "__main__":
    lambda_handler('', '')
