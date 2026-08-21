variable "project_name" {
  description = "Project name prefix for all resources"
  type        = string
  default     = "fintech-devsecops"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "az_count" {
  description = "Number of availability zones to use"
  type        = number
  default     = 2
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-south-1"
}

variable "cluster_name" {
  description = "EKS cluster name for subnet tagging"
  type        = string
  default     = "fintech-devsecops-eks"
}

variable "flow_log_retention_days" {
  description = "CloudWatch log retention in days for VPC Flow Logs"
  type        = number
  default     = 90
}

variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default = {
    Project     = "fintech-devsecops"
    Environment = "production"
    ManagedBy   = "terraform"
    Compliance  = "pci-dss"
  }
}
