variable "license_key" {
  type        = string
  description = "Your New Relic license key. Required to send logs to New Relic Logging."
  sensitive   = true
}

variable "log_type" {
  type        = string
  description = "Your New Relic logtype. You may omit it when deploying the function."
  default     = ""
}

variable "debug_enabled" {
  type        = string
  description = "A boolean to determine if you want to output debug messages in the CloudWatch console"
  default     = "false"
}

variable "environment" {
  type        = string
  description = "Environment that will be used for naming the resources"
}

variable "project_name" {
  type        = string
  description = "Project name that will be included in resources names"
}

variable "filter_prefix" {
  type        = string
  description = "Filter prefix for files in s3 bucket"
  default     = "AWSLogs/"
}

variable "filter_suffix" {
  type        = string
  description = "Filter prefix for files in s3 bucket"
  default     = ".log.gz"
}

variable "bucket_name" {
  type        = string
  description = "s3 bucket name that should be watched for new files"
}

variable "bucket_arn" {
  type        = string
  description = "s3 bucket arn that should be watched for new files"
}
