# AWS Lambda for sending logs from S3 to New Relic
This is a forked repository from New Relic's AWS S3 Log Ingestion Lambda.

`s3-log-ingestion-lambda` is an AWS Serverless application that sends log data from an S3 bucket of your choice to New Relic.

## Requirements

Install serverless
```
npm install -g serverless
serverless plugin install -n serverless-python-requirements
npm install
```

## Package

You need a New Relic license key. Export the following variables with the appropriate environment and bucket name, then package the application:
```
export LICENSE_KEY=<LICENSE_KEY>
export S3_BUCKET_NAME=teachstone-alb-logs-int-red
export LOG_TYPE=elb
export DEBUG_ENABLED=true
export ADDITIONAL_ATTRIBUTES='{"environment": "int"}'
export ENVIRONMENT="int"
export S3_CLOUD_TRAIL_LOG_PATTERN=""
export S3_IGNORE_PATTERN=""
export BATCH_SIZE_FACTOR=""
export AWS_PROFILE=
export S3_PREFIX=

# package
serverless package
```

## Deploy

To deploy, export your AWS credentials and run:
```
serverless deploy --region YOUR_AWS_REGION
```
