# Helm Charts

## Post-Terraform Wiring

After `terraform apply` completes, the following values must be populated before the first ArgoCD sync.

### 1. ECR Repository URLs

Get the ECR URLs from Terraform output:

```bash
terraform -chdir=infrastructure/terraform output ecr_repository_urls
```

Update `image.repository` in:
- `helm/charts/backend/values.yaml`
- `helm/charts/frontend/values.yaml`

### 2. RDS Secret ARN

```bash
terraform -chdir=infrastructure/terraform output rds_secret_arn
```

Set `externalSecret.rdsSecretName` in `helm/charts/backend/values.yaml` to the Secrets Manager secret name (not the full ARN).

### 3. IRSA Role ARNs

Update the `eks.amazonaws.com/role-arn` annotations in `helm/argocd/app-of-apps/values.yaml`:

| App | Terraform Output |
|-----|-----------------|
| `aws-load-balancer-controller` | `terraform output aws_lb_controller_role_arn` |
| `external-secrets` | `terraform output external_secrets_role_arn` |
| `cluster-autoscaler` | `terraform output cluster_autoscaler_role_arn` |
| `external-dns` | `terraform output external_dns_role_arn` |

### 4. Route53, ACM, and DNS

After `terraform apply`, set the NS records from `route53_name_servers` output at your domain registrar. The ACM wildcard certificate (`*.fictional-engine.online`) is created and validated automatically via Route53.

```bash
terraform -chdir=infrastructure/terraform output route53_name_servers
terraform -chdir=infrastructure/terraform output acm_certificate_arn
```

Set `alb.ingress.kubernetes.io/certificate-arn` in `helm/charts/frontend/values.yaml`.

### 5. Ingress Inbound CIDRs

The frontend ALB ingress restricts access by source IP. Update `alb.ingress.kubernetes.io/inbound-cidrs` in the `ingress.annotations` section of `helm/charts/frontend/values.yaml` to the CIDR(s) that should be allowed to reach the application through the public ALB (e.g., your office or VPN IP).

## Initial Deployment

After completing the post-Terraform wiring above, connect to the cluster and deploy:

```bash
aws eks update-kubeconfig --name fictional-engine-production --region us-east-1
```

Install ArgoCD:

```bash
kubectl create namespace argocd
helm install argocd argo-cd --repo https://argoproj.github.io/argo-helm --namespace argocd --wait
```

Configure private repository access (the repository uses SSH):

```bash
ssh-keygen -t ed25519 -f /tmp/argocd-deploy-key -N ""
```

Add the public key (`cat /tmp/argocd-deploy-key.pub`) as a read-only deploy key in **GitHub → Repo → Settings → Deploy keys**.

Create the repo secret in ArgoCD:

```bash
kubectl create secret generic private-repo \
  --namespace argocd \
  --from-literal=type=git \
  --from-literal=url=git@github.com:dimitrije-janic/fictional-engine.git \
  --from-file=sshPrivateKey=/tmp/argocd-deploy-key

kubectl label secret private-repo -n argocd argocd.argoproj.io/secret-type=repository

rm /tmp/argocd-deploy-key /tmp/argocd-deploy-key.pub
```

Deploy the bootstrap chart (this creates the root Application that manages the app-of-apps):

```bash
helm install bootstrap helm/argocd/bootstrap --namespace argocd
```

ArgoCD will now sync the app-of-apps chart from the Git repository, which in turn creates and manages all child applications defined in `helm/argocd/app-of-apps/values.yaml`.

Retrieve the ArgoCD admin password:

```bash
kubectl get secret -n argocd argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

Port-forward to access the ArgoCD UI:

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

## Chart Structure

```
helm/
  charts/
    backend/         — FastAPI application
    frontend/        — React + nginx
    cluster-config/  — Cluster-wide resources (gp3 StorageClass, default-deny NetworkPolicy)
  argocd/
    bootstrap/       — Bootstrap chart that creates the root Application
    app-of-apps/     — Generates child Application resources for all apps
```
