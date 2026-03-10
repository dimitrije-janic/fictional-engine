variable "region" {
  description = "AWS region"
  type        = string
}

variable "project" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
}

variable "single_nat_gateway" {
  description = "Use a single NAT gateway (cost optimization for non-prod)"
  type        = bool
  default     = false
}

variable "kubernetes_version" {
  description = "EKS Kubernetes version"
  type        = string
}

variable "node_instance_type" {
  description = "EC2 instance type for EKS nodes"
  type        = string
}

variable "node_min_size" {
  description = "Minimum number of EKS nodes"
  type        = number
}

variable "node_max_size" {
  description = "Maximum number of EKS nodes"
  type        = number
}

variable "node_desired_size" {
  description = "Desired number of EKS nodes"
  type        = number
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
}

variable "db_name" {
  description = "RDS database name"
  type        = string
}

variable "rds_multi_az" {
  description = "Enable multi-AZ for RDS"
  type        = bool
  default     = false
}

variable "rds_backup_retention" {
  description = "RDS backup retention period in days"
  type        = number
  default     = 7
}

variable "rds_deletion_protection" {
  description = "Enable RDS deletion protection"
  type        = bool
  default     = true
}

variable "rds_skip_final_snapshot" {
  description = "Skip final snapshot on RDS deletion"
  type        = bool
  default     = false
}

variable "github_org" {
  description = "GitHub organization or username"
  type        = string
}

variable "github_repo" {
  description = "GitHub repository name"
  type        = string
}

variable "domain_name" {
  description = "Domain name for Route53 hosted zone"
  type        = string
}

variable "eks_public_access_cidrs" {
  description = "List of CIDRs allowed to access the EKS API endpoint publicly"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "eks_upgrade_support_type" {
  description = "EKS upgrade policy (STANDARD, EXTENDED)"
  type        = string
  default     = "STANDARD"
}

variable "ecr_repositories" {
  description = "List of ECR repository names to create"
  type        = list(string)
}
