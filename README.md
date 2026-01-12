[![Community Plus header](https://github.com/newrelic/opensource-website/raw/master/src/images/categories/Community_Plus.png)](https://opensource.newrelic.com/oss-category/#community-plus)

# AWS Lambda for sending logs from S3 to New Relic

`s3-log-ingestion-lambda` is an AWS Serverless application that sends log data from an S3 bucket of your choice to New Relic.

## Changes from original

- Avail meaningful `timestamp`
    - In original implementation, `timestamp` is set to the time when Lambda is invoked. With this implementation, `timestamp` is set to the time when log record is generated.
    - `date` and `time` attributes are removed.
- In Lambda, replace date and time each of log record, to timestamp in ISO8601 format
- In New Relic, use timestamp in ISO8601 format as `timestamp`
    - You have to define Log parsing rule in New Relic. Read following [Setup in New Relic](#setup-in-new-relicrequired-for-this-repository) section.

## Requirements

To forward data to New Relic you need access to a [New Relic License Key](https://docs.newrelic.com/docs/accounts/install-new-relic/account-setup/license-key).

## Install

To install and configure the New Relic S3 log shipper Lambda, [see our documentation](https://docs.newrelic.com/docs/logs/enable-new-relic-logs/1-enable-logs/aws-lambda-sending-logs-s3).

**Note: Use [Manual install using Serverless Framework](https://docs.newrelic.com/docs/logs/forward-logs/aws-lambda-sending-logs-s3/#serverless-install)**

Example(replace YOUR_XXX with your values):

```shell
git clone https://github.com/netmarkjp/aws_s3_log_ingestion_lambda.git
cd aws_s3_log_ingestion_lambda

# sls(serverless framework) parameters
export SERVICE_NAME=YOUR_SERVICE_NAME

# function parameters
export LICENSE_KEY=YOUR_LICENSE_KEY
export LOG_TYPE=cloudfront-web-timestamp
export DEBUG_ENABLED=false
export S3_CLOUDTRAIL_LOG_PATTERN=""
export S3_IGNORE_PATTERN=""
export BATCH_SIZE_FACTOR=""
export ADDITIONAL_ATTRIBUTES='{"aws.accountId": "YOUR_ACCOUNT_ID", "aws.region": "YOUR_REGION"}'

# event parameters
export S3_BUCKET_NAME=YOUR_LOG_BUCKET_NAME
export S3_PREFIX=""

# install serverless plugins if needed
npx serverless plugin install -n serverless-python-requirements
npx serverless plugin install -n serverless-better-credentials

# deploy
npx serverless deploy --region YOUR_REGION --config serverless.yml
```

## Setup in New Relic(required for this repository)

With web browser, go to [Logs > Parsing](https://one.newrelic.com/logger/log-parsing) and `Create parsing rule`.

- Name: `cloudfront-web-timestamp`
- Field to parse: `message`
- Filter logs based on NRQL: `logtype='cloudfront-web-timestamp'`
- Parsing rule: ```^%{TIMESTAMP_ISO8601:timestamp}%{SPACE}%{NOTSPACE:x_edge_location}%{SPACE}%{NOTSPACE:sc_bytes}%{SPACE}%{NOTSPACE:c_ip}%{SPACE}%{NOTSPACE:cs_method}%{SPACE}%{NOTSPACE:cs_host}%{SPACE}%{NOTSPACE:cs_uri_stem}%{SPACE}%{NOTSPACE:sc_status}%{SPACE}%{NOTSPACE:cs_referer}%{SPACE}%{NOTSPACE:cs_user_agent}%{SPACE}%{NOTSPACE:cs_uri_query}%{SPACE}%{NOTSPACE:cs_Cookie}%{SPACE}%{NOTSPACE:x_edge_result_type}%{SPACE}%{NOTSPACE:x_edge_request_id}%{SPACE}%{NOTSPACE:x_host_header}%{SPACE}%{NOTSPACE:cs_protocol}%{SPACE}%{NOTSPACE:cs_bytes}%{SPACE}%{NOTSPACE:time_taken}%{SPACE}%{NOTSPACE:x_forwarded_for}%{SPACE}%{NOTSPACE:ssl_protocol}%{SPACE}%{NOTSPACE:ssl_cipher}%{SPACE}%{NOTSPACE:x_edge_response_result_type}%{SPACE}%{NOTSPACE:cs_protocol_version}%{SPACE}%{NOTSPACE:fle_status}%{SPACE}%{NOTSPACE:fle_encrypted_fields}%{SPACE}%{NOTSPACE:c_port}%{SPACE}%{NOTSPACE:time_to_first_byte}%{SPACE}%{NOTSPACE:x_edge_detailed_result_type}%{SPACE}%{NOTSPACE:sc_content_type}%{SPACE}%{NOTSPACE:sc_content_len}%{SPACE}%{NOTSPACE:sc_range_start}%{SPACE}%{NOTSPACE:sc_range_end}```

`Parsing rule` in one line.
Based on builtin logtype `cloudfront-web`.
https://docs.newrelic.com/docs/logs/ui-data/built-log-parsing-rules/#cloudfront

From `cloudfront-web`, replace `^%{NOTSPACE:date}%{SPACE}%{NOTSPACE:time}` to `^%{TIMESTAMP_ISO8601:timestamp}`.

Note: Because of the restiction of New Relic parsing rule length, we cannot **append** timestamp. So we have to **replace** these attributes

## Support

New Relic hosts and moderates an online forum where customers can interact with New Relic employees as well as other customers to get help and share best practices. Like all official New Relic open source projects, there's a [related Community topic in the New Relic Explorers Hub](https://discuss.newrelic.com/t/aws-s3-log-ingestion-lambda/104986).

## Contributing

Contributions to improve s3-log-ingestion-lambda are encouraged! Keep in mind when you submit your pull request, you'll need to sign the CLA via the click-through using CLA-Assistant. You only have to sign the CLA one time per project.

To execute our corporate CLA, which is required if your contribution is on behalf of a company, or if you have any questions, please drop us an email at opensource@newrelic.com.

## Developers

For more information about how to contribute from the developer point of view,
we recommend you to take a look to the [DEVELOPER.md](./DEVELOPER.md) that 
contains most of the info you'll need.

## License
`s3-log-ingestion-lambda` is licensed under the [Apache 2.0](http://apache.org/licenses/LICENSE-2.0.txt) License. The s3-log-ingestion-lambda also uses source code from third party libraries. Full details on which libraries are used and the terms under which they are licensed can be found in the third party notices document