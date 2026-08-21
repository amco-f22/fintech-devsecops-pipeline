# ==============================================================================
# Production Environment — Fintech DevSecOps Pipeline
# ==============================================================================
# Composes VPC + EKS + ECR modules into a hardened production environment
# targeting SecurePay's merchant payment infrastructure requirements.
# ==============================================================================

terraform {
  required_version = ">= 1.9.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Remote state in S3 with DynamoDB locking
  backend "s3" {
    bucket         = "fintech-devsecops-terraform-state"
    key            = "production/terraform.tfstate"
    region         = "ap-south-1"
    encrypt        = true
    dynamodb_table = "fintech-devsecops-terraform-lock"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "fintech-devsecops"
      Environment = "production"
      ManagedBy   = "terraform"
      Compliance  = "pci-dss"
    }
  }
}

# --- Locals ---

locals {
  project_name = "fintech-devsecops"
  cluster_name = "${local.project_name}-eks"

  tags = {
    Project     = local.project_name
    Environment = "production"
    ManagedBy   = "terraform"
    Compliance  = "pci-dss"
  }
}

# --- VPC ---

module "vpc" {
  source = "../../modules/vpc"

  project_name            = local.project_name
  vpc_cidr                = var.vpc_cidr
  az_count                = var.az_count
  aws_region              = var.aws_region
  cluster_name            = local.cluster_name
  flow_log_retention_days = 90
  tags                    = local.tags
}

# --- EKS ---

module "eks" {
  source = "../../modules/eks"

  cluster_name       = local.cluster_name
  kubernetes_version = var.kubernetes_version
  vpc_id             = module.vpc.vpc_id
  vpc_cidr           = module.vpc.vpc_cidr_block
  private_subnet_ids = module.vpc.private_subnet_ids

  node_instance_types = var.node_instance_types
  node_desired_size   = var.node_desired_size
  node_min_size       = var.node_min_size
  node_max_size       = var.node_max_size
  node_disk_size      = var.node_disk_size

  tags = local.tags
}

# --- ECR ---

module "ecr" {
  source = "../../modules/ecr"

  repository_name = "${local.project_name}/webhook-service"
  tags            = local.tags
}
