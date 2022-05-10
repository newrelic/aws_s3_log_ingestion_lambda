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
  memory_size      = 128
  role             = aws_iam_role.lambda.arn
  layers           = ["${aws_lambda_layer_version.python38_ingestion_lambda.arn}"]
  environment {
    variables = {
      LICENSE_KEY   = var.license_key
      LOG_TYPE      = var.log_type
      DEBUG_ENABLED = var.debug_enabled
    }
  }
}


resource "aws_lambda_layer_version" "python38_ingestion_lambda" {
  filename            = "${path.module}/src/python38-requirements.zip"
  layer_name          = "Python38-requirements"
  source_code_hash    = filebase64sha256("${path.module}/packages/python38-requirements.zip")
  compatible_runtimes = ["python3.8", ]
}
