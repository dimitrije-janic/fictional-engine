# CI/CD Pipelines

## Overview

```
Pull Request → CI (SAST + Test + Lint + Build) → validate only, no push
Push to main → CI (SAST + Test + Lint + Build + Push) → images tagged sha-<commit>
Git tag      → Release (Retag + Deploy) → images retagged with version, Helm values updated
```

## Workflows

### CI (`ci.yml`)

**Triggers:** push to `main`, pull requests to `main`, manual dispatch
**Path filter:** only runs when `backend/**` or `frontend/**` changes

| Job | Name | Purpose |
|-----|------|---------|
| `sast` | Static Analysis | Runs Semgrep with Python, React, security-audit, and OWASP top-ten rulesets |
| `backend-test` | Test Backend | Runs unit tests against PostgreSQL service container, publishes JUnit report |
| `frontend-lint` | Lint Frontend | Runs ESLint on the React codebase |
| `backend-build` | Build Backend | Builds Docker image, pushes to ECR on main (build-only on PRs) |
| `frontend-build` | Build Frontend | Builds Docker image, pushes to ECR on main (build-only on PRs) |

**Flow:** `sast` + `backend-test` → `backend-build`, `sast` + `frontend-lint` → `frontend-build` (parallel branches)

Backend tests run against a PostgreSQL 15 service container with `pytest -m "not integration"` (integration tests require Docker-in-Docker and are run locally). Test results are published as a GitHub check run via `dorny/test-reporter`.

On pull requests, images are built but **not pushed** — validates the Dockerfile and build process only.

### Build Docker Image (`build-docker.yml`)

**Trigger:** reusable workflow (called by `ci.yml`)

**Inputs:**
- `service-name` — which service to build (`backend` or `frontend`)
- `push` — whether to push the image to ECR

**Steps:**
1. Authenticate to AWS via OIDC (`secrets.AWS_IAM_ROLE`)
2. Login to Amazon ECR
3. Build image with Docker Buildx
4. Tag with `sha-<7-char commit hash>`
5. Push to `<ecr-registry>/<repo-name>/<service-name>` (if `push: true`)

### Release (`release.yml`)

**Trigger:** any git tag push (e.g., `git tag v1.2.0 && git push origin v1.2.0`)

| Job | Name | Purpose |
|-----|------|---------|
| `retag` | Retag | Adds the version tag to existing SHA-tagged images in ECR (no rebuild) |
| `deploy` | Deploy | Updates Helm chart values with new image tag and commits to main |

**Flow:** `retag` (backend + frontend in parallel via matrix) → `deploy`

**Retag** finds the image tagged `sha-<commit>` in ECR and adds the release tag (e.g., `v1.2.0`) to the same manifest — no rebuild required.

**Deploy** updates `image.tag` in both `helm/charts/backend/values.yaml` and `helm/charts/frontend/values.yaml` using `yq`, then commits with `[skip ci]` to avoid triggering another CI run. ArgoCD detects the commit and syncs the new image tag.

## Authentication

All workflows use **OIDC federation** — no stored AWS credentials. The GitHub Actions runner assumes `secrets.AWS_IAM_ROLE` via `aws-actions/configure-aws-credentials`.

**Required repository variables:**
- `AWS_IAM_ROLE` — IAM role ARN for GitHub Actions OIDC (`terraform output github_actions_role_arn`)
- `AWS_REGION` — AWS region (e.g., `us-east-1`)

## Image Tagging Strategy

```
Push to main  → sha-abc1234        (mutable, overwritten on next push)
Git tag       → sha-abc1234, v1.2.0 (version tag added to same image)
```

Images are never rebuilt for releases — the release workflow retags the already-tested SHA image.
