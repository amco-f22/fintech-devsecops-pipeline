variable "repository_name" {
  description = "ECR repository name"
  type        = string
  default     = "fintech-devsecops/webhook-service"
}

variable "kms_key_arn" {
  description = "KMS key ARN for image encryption"
  type        = string
  default     = ""
}

variable "tags" {
  description = "Common tags"
  type        = map(string)
  default     = {}
}
