[![Community Plus header](https://github.com/newrelic/opensource-website/raw/master/src/images/categories/Community_Plus.png)](https://opensource.newrelic.com/oss-category/#community-plus)

# AWS Lambda for sending logs from S3 to New Relic

`s3-log-ingestion-lambda` is an AWS Serverless application that sends log data from an S3 bucket of your choice to New Relic.

## Requirements

To forward data to New Relic you need access to a [New Relic License Key](https://docs.newrelic.com/docs/accounts/install-new-relic/account-setup/license-key).

## Install

To install and configure the New Relic S3 log shipper Lambda, [see our documentation](https://docs.newrelic.com/docs/logs/enable-new-relic-logs/1-enable-logs/aws-lambda-sending-logs-s3).


## Working with terraform

You can also use it as a module in terraform:
```

module "newrelic_s3_log_ingestion" {
  source        = "git@github.com:unhaggle/aws_s3_log_ingestion_lambda.git?ref=terraform_support"
  project_name  = var.project_name
  environment   = local.environment
  license_key   = data.aws_ssm_parameter.newrelic_license_key.value
  debug_enabled = "false"
  bucket_name   = aws_s3_bucket.lb_logs.id
  bucket_arn    = aws_s3_bucket.lb_logs.arn
}

```

If there are any changes required regarding lambda packages, please update layer-python38-requirements and then rebuild using `build.sh`

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