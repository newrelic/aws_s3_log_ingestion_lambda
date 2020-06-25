[![Community Project header](https://github.com/newrelic/open-source-office/raw/master/examples/categories/images/Community_Project.png)](https://github.com/newrelic/open-source-office/blob/master/examples/categories/index.md#community-project)

# AWS Lambda for sending logs from S3 to New Relic

`s3-log-ingestion-lambda` is an AWS Serverless application that sends log data from an S3 bucket of your choice to New Relic.

## Requirements

To forward data to New Relic you need access to a [New Relic License Key](https://docs.newrelic.com/docs/accounts/install-new-relic/account-setup/license-key).

## Installation

To install and configure the New Relic S3 log shipper Lambda, [see our documentation](https://docs.newrelic.com/docs/logs/enable-new-relic-logs/1-enable-logs/aws-lambda-sending-logs-s3).

## Configure the Lambda using Serverless

Follow these steps below to deploy the log ingestion function manually. 

1. Clone this repository: `git clone <REPO>`
2. Install Serverless: `npm install -g serverless`
3. Install the `serverless-python-requirements` plugin: `npm install`
4. If not running Linux, [install Docker](https://docs.docker.com/install/) and keep it running.
5. Set the `LICENSE_KEY` environment variable: `export LICENSE_KEY=your-license-key-here`
6. Set the optional `logtype` environment variable: `export logtype=your-log-type-here`
7. Set the S3_BUCKET_NAME environment variable: `export S3_BUCKET_NAME=your-s3-bucket-name`
8. [Optional] You can send logs from a specific location in the bucket only. Set the S3_Prefix (subdirectory name) `export S3_PREFIX=your-s3-subdirectory-name`
9. Deploy the function: `serverless deploy`
 
## Troubleshooting

```bash:
 Error: docker: Cannot connect to the Docker daemon at unix:///var/run/docker.sock. Is the docker daemon running?.
```
When using serverless to deploy the lambda from your machine, this error message may occur. This may mean either docker is not running or it has not been correctly set up. Please ensure docker is runnig on your machine when deploying the lambda using serverless.

```bash:
An error occurred when creating the trigger: Configurations overlap. Configurations on the same bucket cannot share a common event type.
```
If this error message appears while adding a Lambda "Trigger", ensure your s3 does not have another event of the same type on the bucket.
Ie, your s3 bucket cannot have multiple "all object create events" events. 

## Support

New Relic hosts and moderates an online forum where customers can interact with New Relic employees as well as other customers to get help and share best practices. Like all official New Relic open source projects, there's a related Community topic in the New Relic Explorers Hub.

## Contributing

Contributions to improve s3-log-ingestion-lambda are encouraged! Keep in mind when you submit your pull request, you'll need to sign the CLA via the click-through using CLA-Assistant. You only have to sign the CLA one time per project.

To execute our corporate CLA, which is required if your contribution is on behalf of a company, or if you have any questions, please drop us an email at opensource@newrelic.com.

## License
`s3-log-ingestion-lambda` is licensed under the [Apache 2.0](http://apache.org/licenses/LICENSE-2.0.txt) License. The s3-log-ingestion-lambda also uses source code from third party libraries. Full details on which libraries are used and the terms under which they are licensed can be found in the third party notices document.
