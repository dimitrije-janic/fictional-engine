# fictional-engine

Server Inventory Management System — a full-stack application for tracking servers across data centers, deployed on AWS EKS with GitOps.

## Architecture

| Component | Tech | Description |
|-----------|------|-------------|
| Backend | Python, FastAPI, psycopg2 | REST API with CRUD on `/servers`, health check on `/health` |
| Frontend | React, Vite, nginx | SPA with nginx reverse proxy to backend |
| CLI | Python, Click | Command-line client for the API |
| Database | PostgreSQL 15 (RDS) | Raw SQL, no ORM. Multi-AZ in production |
| Infrastructure | Terraform | VPC, EKS, RDS, ECR, Route53, ACM, IAM |
| Orchestration | Kubernetes (EKS) | Managed node groups, Cluster Autoscaler |
| GitOps | ArgoCD | App-of-apps pattern, auto-sync with prune |
| CI/CD | GitHub Actions | SAST, test, lint, Docker build, ECR push, manifest update |
| Monitoring | kube-prometheus-stack | Prometheus, Grafana, AlertManager |
| Logging | Loki + Alloy | Centralized log aggregation with JSON structured logs |

## Repository Structure

```
├── backend/                 # FastAPI API + CLI tool
├── frontend/                # React SPA
├── infrastructure/
│   └── terraform/           # AWS infrastructure (VPC, EKS, RDS, ECR, Route53, ACM, IAM)
├── helm/
│   ├── charts/
│   │   ├── backend/         # Backend Helm chart
│   │   ├── frontend/        # Frontend Helm chart
│   │   └── cluster-config/  # Cluster-wide resources (gp3 StorageClass, default-deny NetworkPolicy)
│   └── argocd/
│       ├── bootstrap/       # Root ArgoCD Application
│       └── app-of-apps/     # All cluster applications
├── .github/
│   └── workflows/           # CI/CD pipelines
└── docker-compose.yml       # Local development stack
```

## Deploying from Zero

### Prerequisites

- AWS CLI configured with appropriate IAM permissions
- Terraform ~> 1.14.0
- kubectl
- Helm 3
- A GitHub repository with Actions enabled

### Step 1: Provision Infrastructure

Bootstrap the Terraform state backend, then create all AWS resources.

See [infrastructure/terraform/README.md](infrastructure/terraform/README.md) for full instructions.

```bash
cd infrastructure/terraform/bootstrap
terraform init && terraform apply

cd ..
terraform init -backend-config=backend-config/production.config
terraform plan -var-file=tfvars/production.tfvars
terraform apply -var-file=tfvars/production.tfvars
```

This creates: VPC, EKS cluster, RDS instance (encrypted), ECR repositories, Route53 hosted zone, ACM wildcard certificate, and all IAM roles.

### Step 2: Configure GitHub Actions

Set the following **repository variables** in GitHub (Settings > Secrets and variables > Actions > Variables):

| Variable | Value |
|----------|-------|
| `AWS_IAM_ROLE` | `terraform output github_actions_role_arn` |
| `AWS_REGION` | `us-east-1` |

### Step 3: Wire Helm Values

Populate ECR URLs, RDS secret, IRSA role ARNs, and ingress inbound CIDRs from Terraform outputs into Helm chart values.

See [helm/README.md](helm/README.md) for the complete wiring checklist.

### Step 4: Bootstrap ArgoCD

Connect to the cluster and install ArgoCD, then deploy the app-of-apps.

See [helm/README.md](helm/README.md) for detailed instructions.

```bash
aws eks update-kubeconfig --name fictional-engine-production --region us-east-1

# Install ArgoCD
kubectl create namespace argocd
helm install argocd argo-cd --repo https://argoproj.github.io/argo-helm --namespace argocd --wait

# Configure repo access (SSH deploy key)
# ... see helm/README.md

# Deploy the bootstrap chart
helm install bootstrap helm/argocd/bootstrap --namespace argocd
```

ArgoCD will sync all applications: backend, frontend, cluster-config, AWS Load Balancer Controller, external-secrets, cluster-autoscaler, external-dns, metrics-server, Loki, Alloy, and kube-prometheus-stack.

### Step 5: First Release

Push code, tag a release, and the CI/CD pipeline handles the rest.

See [.github/workflows/README.md](.github/workflows/README.md) for pipeline documentation.

```bash
git tag v1.0.0
git push origin v1.0.0
```

This triggers: image retag in ECR, Helm values update, ArgoCD sync.

## Local Development

```bash
# Start full stack (API + DB + Frontend)
docker compose up -d

# Backend only with hot reload
docker compose up -d db
cd backend && pip install -r requirements.txt
uvicorn api.main:app --reload

# Frontend only with hot reload
cd frontend && npm ci && npm run dev

# Unit tests (requires test DB)
docker compose --profile test up -d db-test
export TEST_DATABASE_URL=postgresql://postgres:postgres@localhost:5433/inventory_test
cd backend && pytest -v -m "not integration"

# Integration tests (requires full Docker stack)
cd backend && pytest -v -m integration
```

## Documentation Index

| Document | Contents |
|----------|----------|
| [backend/README.md](backend/README.md) | API specification, CLI usage, data model |
| [frontend/README.md](frontend/README.md) | Frontend setup and nginx config |
| [infrastructure/terraform/README.md](infrastructure/terraform/README.md) | Terraform structure, bootstrap, plan/apply, outputs |
| [helm/README.md](helm/README.md) | Post-Terraform wiring, ArgoCD bootstrap, chart structure |
| [.github/workflows/README.md](.github/workflows/README.md) | CI/CD pipeline documentation |
