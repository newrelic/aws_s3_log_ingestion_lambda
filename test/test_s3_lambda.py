import gzip
import json
import os
import pprint
import pytest
import uuid

from base64 import b64decode
from mock import patch
from src import handler
from test.mock_http_response import MockHttpResponse
from test.mock_aws_events import create_mock_aws_event

import asyncio
from asynctest import CoroutineMock

import boto3
import botocore


US_URL = "https://log-api.newrelic.com/log/v1"
EU_URL = "https://log-api.eu.newrelic.com/log/v1"
OTHER_URL = "http://some-other-endpoint/logs/v1"
STAGING_URL = "https://staging-log-api.newrelic.com/log/v1"


nr_license_key = os.environ["LICENSE_KEY"]
timestamp = 1548935491174
license_key = "testlicensekey"
license_key_eu = "eutestlicensekey"
log_group_name = "/aws/lambda/sam-node-test-dev-triggered"
log_stream_name = "2019/01/31/[$LATEST]fe9b6a749a854acb95af7951c44a79e0"

context = type("SomeTypeOfContext", (object,), {})()
context.function_name = "function-1"
context.invoked_function_arn = "arn-1"
context.log_group_name = log_group_name
context.log_stream_name = log_stream_name

async def aio_post_response():
    return MockHttpResponse("", 202)


def urlopen_error_response():
    return MockHttpResponse("", 429)


@pytest.fixture(autouse=True)
def set_up():
    # Default environment variables needed by most tests
    os.environ["LICENSE_KEY"] = license_key

    handler.INITIAL_BACKOFF = 0.1


@pytest.fixture
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_aio_post():
    with patch("aiohttp.ClientSession.post", new=CoroutineMock()) as mocked_aio_post:
        yield mocked_aio_post


@patch.dict(
    os.environ,
    clear=True,
)
def test_logging_has_default_nr_endpoint():
    assert handler._get_logging_endpoint() == US_URL


@patch.dict(
    os.environ,
    {
        "NR_LOGGING_ENDPOINT": OTHER_URL,
    },
    clear=True,
)
def test_logging_can_override_nr_endpoint():
    assert handler._get_logging_endpoint() == OTHER_URL


@patch.dict(
    os.environ,
    {
        "LICENSE_KEY": license_key_eu,
    },
    clear=True,
)
def test_logging_has_eu_nr_endpoint():
    assert handler._get_logging_endpoint() == EU_URL


def test_proper_headers_are_added(mock_aio_post):
    mock_aio_post.return_value = aio_post_response()
    message_1 = "Test Message 1"
    event = create_mock_aws_event()

    response = handler.lambda_handler(event, context)

    # Note that header names are somehow lower-cased
    mock_aio_post.assert_called()
    headers = mock_aio_post.call_args[1]["headers"]
    assert headers["X-license-key"] == license_key
    assert headers["X-event-source"] == "logs"
    assert headers["Content-encoding"] == "gzip"
    assert response["statusCode"] == 200
    assert response["message"] == "Uploaded logs to New Relic"


def test_when_first_call_fails_code_should_retry(mock_aio_post):
    # First fail, and then succeed
    mock_aio_post.side_effect = [urlopen_error_response(), aio_post_response()]
    event = create_mock_aws_event()

    response = handler.lambda_handler(event, context)

    assert mock_aio_post.call_count == 2
    assert response["statusCode"] == 200
    assert response["message"] == "Uploaded logs to New Relic"


def test_when_first_two_calls_fail_code_should_retry(mock_aio_post):
    # First two fail, and then third succeeds
    mock_aio_post.side_effect = [
        urlopen_error_response(),
        urlopen_error_response(),
        aio_post_response(),
    ]
    event = create_mock_aws_event()

    response = handler.lambda_handler(event, context)
    print("response:", response)

    assert mock_aio_post.call_count == 3
    assert response["statusCode"] == 200
    assert response["message"] == "Uploaded logs to New Relic"


@patch.dict(
    os.environ,
    {
        "DEBUG_ENABLED": "true"
    },
    clear=True,
)
def test_BadRequestException_no_license_key():
    with pytest.raises(handler.BadRequestException):
        event = create_mock_aws_event(file_name="mock_one_hundred_thousand.json")

        handler.lambda_handler(event, context)


@patch.dict(
    os.environ,
    {
        "LICENSE_KEY": nr_license_key,
        "DEBUG_ENABLED": "false"
    },
    clear=True,
)
def test_one_hundred_thousand_log_lines():

    event = create_mock_aws_event(file_name="mock_one_hundred_thousand.json")

    response = handler.lambda_handler(event, context)
    print("response:", response)

    assert response["statusCode"] == 200
    assert response["message"] == "Uploaded logs to New Relic"


@patch.dict(
    os.environ,
    {
        "LICENSE_KEY": nr_license_key,
        "DEBUG_ENABLED": "false"
    },
    clear=True,
)
def test_two_hundred_fifty_thousand_log_lines():

    event = create_mock_aws_event(file_name="mock_two_hundred_fifty_thousand.json")

    response = handler.lambda_handler(event, context)
    print("response:", response)

    assert response["statusCode"] == 200
    assert response["message"] == "Uploaded logs to New Relic"