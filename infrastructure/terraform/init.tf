terraform {
  required_version = "~> 1.14.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "6.36.0"
    }
  }

  backend "s3" {
    bucket         = "fictional-engine-tf-state"
    region         = "us-east-1"
    dynamodb_table = "fictional-engine-tf-lock"
    encrypt        = true
    # key set via -backend-config=backend-config/<env>.config
  }
}

provider "aws" {
  region = var.region
  default_tags {
    tags = {
      Project     = var.project
      Environment = var.environment
      ManagedBy   = "terraform/fictional-engine"
    }
  }
}
