data "archive_file" "newrelic_s3_log_ingestion_lambda" {
  type        = "zip"
  source_dir  = "${path.module}/src"
  output_path = "${path.module}/tmp/lambda.zip"
}

resource "aws_lambda_function" "newrelic_s3_log_ingestion_lambda" {
  function_name    = "${var.project_name}-${var.environment}-newrelic-s3-log-ingestion-lambda"
  filename         = "${path.module}/tmp/lambda.zip"
  source_code_hash = data.archive_file.newrelic_s3_log_ingestion_lambda.output_base64sha256
  handler          = "handler.lambda_handler"
  runtime          = "python3.8"
  role             = aws_iam_role.lambda.arn

  environment {
    variables = {
      LICENSE_KEY   = var.license_key
      LOG_TYPE      = var.log_type
      DEBUG_ENABLED = var.debug_enabled
    }
  }
}


