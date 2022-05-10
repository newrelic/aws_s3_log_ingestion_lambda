resource "aws_iam_role" "lambda" {
  name               = "${var.project_name}-${var.environment}-newrelic-s3-log-ingestion-lambda"
  path               = "/"
  assume_role_policy = <<POLICY
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
POLICY
}



resource "aws_lambda_permission" "allow_bucket" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.newrelic_s3_log_ingestion_lambda.arn
  principal     = "s3.amazonaws.com"
  source_arn    = var.bucket_arn
}


resource "aws_iam_policy" "bucket_policy" {
  name        = "${var.bucket_name}-allow-get-object"
  path        = "/"
  description = "Allow getting objects from s3"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "s3:GetObject",
        ]
        Effect = "Allow"
        Resource = [
          "arn:aws:s3:::${var.bucket_name}",
          "arn:aws:s3:::${var.bucket_name}/*"
        ]
      },
    ]
  })
}

resource "aws_iam_role_policy_attachment" "watched_bucket_policy" {
  role       = aws_iam_role.lambda.name
  policy_arn = aws_iam_policy.bucket_policy.arn
}

resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = var.bucket_name

  lambda_function {
    lambda_function_arn = aws_lambda_function.newrelic_s3_log_ingestion_lambda.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = var.filter_prefix
    filter_suffix       = var.filter_suffix
  }
  depends_on = [
    aws_lambda_permission.allow_bucket
  ]
}
