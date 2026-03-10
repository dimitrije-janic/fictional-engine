# Infrastructure

Terraform-managed AWS infrastructure for the fictional-engine project.

## Directory Structure

```
infrastructure/terraform/
  init.tf              # Terraform & provider config, S3 backend
  main.tf              # All resource definitions (VPC, EKS, RDS, ECR, Route53, ACM, IAM)
  variables.tf         # Variable declarations
  outputs.tf           # Outputs (cluster name, ECR URLs, IRSA ARNs, ACM cert, Route53, RDS secret)
  backend-config/
    production.config  # State key for production environment
  tfvars/
    production.tfvars  # Variable values for production
  bootstrap/
    main.tf            # One-time setup: S3 state bucket + DynamoDB lock table
```

## Prerequisites

- Terraform ~> 1.14.0
- AWS CLI configured
- Sufficient IAM permissions to create VPC, EKS, RDS, ECR, and IAM resources

## Bootstrap (One-Time)

Before running the main Terraform config, create the S3 bucket and DynamoDB table for remote state:

```bash
cd infrastructure/terraform/bootstrap
terraform init
terraform apply
```

This creates:
- S3 bucket `fictional-engine-tf-state` (versioned, KMS-encrypted, no public access)
- DynamoDB table `fictional-engine-tf-lock` for state locking

Both are shared across all environments — isolation is done via separate state keys.

## Init

Initialize Terraform with the appropriate backend config for your target environment:

```bash
cd infrastructure/terraform
terraform init -backend-config=backend-config/production.config
```

## Plan & Apply

Always pass the matching `-var-file` for your environment:

```bash
terraform plan  -var-file=tfvars/production.tfvars
terraform apply -var-file=tfvars/production.tfvars
```

## What Gets Created

| Resource | Description |
|----------|-------------|
| **VPC** | 3 AZs, public/private/database subnets, NAT gateways (one per AZ in production) |
| **EKS** | Managed Kubernetes cluster with managed node group, IRSA enabled, control plane logging, restricted API endpoint, VPC CNI with NetworkPolicy support, CoreDNS/kube-proxy/EBS CSI addons |
| **RDS** | PostgreSQL 15, multi-AZ in production, storage encryption, credentials auto-managed via Secrets Manager |
| **ECR** | Container registries for backend and frontend (immutable tags, 20-image lifecycle) |
| **Route53** | Hosted zone for `fictional-engine.online` |
| **ACM** | Wildcard certificate for `*.fictional-engine.online` with DNS validation |
| **IAM** | GitHub OIDC provider + role, IRSA roles for LB Controller, External Secrets, Cluster Autoscaler, EBS CSI, external-dns |

## Outputs

After `terraform apply`, the following outputs are available:

| Output | Usage |
|--------|-------|
| `vpc_id` | VPC ID for reference |
| `eks_cluster_name` | `aws eks update-kubeconfig --name <value>` |
| `ecr_repository_urls` | Set `image.repository` in Helm chart values |
| `github_actions_role_arn` | Configure as `AWS_ROLE_ARN` secret in GitHub |
| `aws_lb_controller_role_arn` | IRSA annotation for AWS Load Balancer Controller |
| `external_secrets_role_arn` | IRSA annotation for External Secrets Operator |
| `cluster_autoscaler_role_arn` | IRSA annotation for Cluster Autoscaler |
| `ebs_csi_role_arn` | IRSA annotation for EBS CSI Driver |
| `acm_certificate_arn` | Certificate ARN for ALB ingress annotations |
| `external_dns_role_arn` | IRSA annotation for external-dns |
| `route53_zone_id` | Hosted zone ID for DNS management |
| `route53_name_servers` | NS records to set at domain registrar |
| `rds_secret_arn` | Secrets Manager ARN for RDS credentials |


## Adding a New Environment

1. Create `backend-config/<env>.config` with a unique state key
2. Create `tfvars/<env>.tfvars` with environment-specific values
3. Run `terraform init -backend-config=backend-config/<env>.config`
4. Run `terraform apply -var-file=tfvars/<env>.tfvars`
