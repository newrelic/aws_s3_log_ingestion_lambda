# Developer

This project uses [SAM](https://aws.amazon.com/serverless/sam/) tool for build,
run locally, package and publish.

There is a serverless file to play locally as well, but here we will focus on
the [SAM](https://aws.amazon.com/serverless/sam/) way of doing it.

## Requirements

- Make

### Local run / build

- Docker
- AWS Account
- AWS Profile configured on your computer, remember that AWS uses the `default`
  profile unless you specify it. You can specify usign `AWS_PROFILE` enviroment
  variable.
- [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-reference.html#serverless-sam-cli)

### Package

- An AWS S3 bucket where the package will be uploaded

### Publishing

- For personal publishing is mandatory to update the function name on the
  `template.yml` file to avoid collide with the New Relic official release of
  this application.

### Deploy

- AWS Account and enough permissions to do the deploy, generated template will
  need IAM capabilities.

## Building it locally

This will generate an image of the lambda application using a docker container
that you will be able to run locally.

Just run `make build`.

## Running locally

You should have built the image locally as mentioned in the previous step.

Then you need to have a "sample" event of a file in an S3 bucket so we can use
it, we provide a sample one in the test/mock.json but it wouldn't work if you
haven't access to the given S3 bucket.

Then just run `LICENSE_KEY=<YOUR_NEW_RELIC_LICENSE_KEY> TEST_FILE="./test/mock.json" make run-local` to run it locally.

## Packaging

Run `BUCKET=<S3_BUCKET_NAME> REGION=<S3_BUCKET_AWS_REGION> make package`

## Deploying

Run `REGION=<THE_REGION_YOU_WANT> STACK_NAME=<THE_STACK_NAME_YOU_WANT> make deploy`

## Publishing

Run `REGION=<SAR_AWS_REGION> make publish` to publish your package. Remember to
update the function name before publishing it to do not collide with the New
Relic official application.
