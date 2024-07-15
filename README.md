[![Community Plus header](https://github.com/newrelic/opensource-website/raw/master/src/images/categories/Community_Plus.png)](https://opensource.newrelic.com/oss-category/#community-plus)

# AWS Lambda for sending logs from S3 to New Relic via SNS (multiple lambda handlers can be ingesting same data)

`s3-sns-log-ingestion-lambda` is an AWS Serverless application that sends log data from an S3 bucket of your choice to New Relic via SNS topic.

## Requirements

To forward data to New Relic you need access to a [New Relic License Key](https://docs.newrelic.com/docs/accounts/install-new-relic/account-setup/license-key).
You will also need an existing S3 bucket and existing SNS topic.

You will need to set the following environment variables

`LICENSE_KEY` - New Relic License ingest key

`LOG_TYPE` - Log type to be sent to New Relic

`DEBUG_ENABLED` - Set to `true` to enable debug logging

`SNS_TOPIC_NAME` - SNS topic name to distribute logs messages to multiple lambda 
handlers

`S3_BUCKET_NAME` - S3 bucket name to read logs from
 
## Install

To install and configure the New Relic S3/SNS log shipper Lambda, [see our documentation](https://docs.newrelic.com/docs/logs/enable-new-relic-logs/1-enable-logs/aws-lambda-sending-logs-s3).

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