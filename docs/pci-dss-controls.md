# PCI-DSS Controls Mapping

This document maps the security controls implemented in the Fintech DevSecOps Pipeline
to specific PCI-DSS requirements. These controls demonstrate how automated DevSecOps
practices enforce compliance in a payment processing environment.

## Requirement 1: Install and Maintain Network Security Controls

| Control | Implementation | Evidence |
|---------|---------------|----------|
| Network segmentation | Private VPC subnets, no public IPs | `terraform/modules/vpc/main.tf` |
| Firewall rules | Security groups restrict ingress to port 443 from VPC CIDR only | `terraform/modules/eks/main.tf` |
| Pod-level isolation | K8s NetworkPolicy restricts ingress/egress per service | `helm/webhook-service/templates/networkpolicy.yaml` |
| No public endpoints | EKS private control plane, ClusterIP services | `terraform/modules/eks/main.tf`, `helm/webhook-service/values.yaml` |
| Internal LB enforcement | OPA policy denies public LoadBalancer without annotation | `policies/network_security.rego` |
| VPC Endpoints | ECR, S3, STS traffic never leaves AWS network | `terraform/modules/vpc/main.tf` |

## Requirement 2: Apply Secure Configurations to All System Components

| Control | Implementation | Evidence |
|---------|---------------|----------|
| No default credentials | OPA policy denies plaintext secrets in env vars | `policies/pci_compliance.rego` |
| IMDSv2 enforcement | Launch template requires http_tokens = "required" | `terraform/modules/eks/main.tf` |
| Non-root containers | Pod security context enforces runAsNonRoot | `helm/webhook-service/values.yaml` |
| Read-only root FS | Container runs with readOnlyRootFilesystem: true | `helm/webhook-service/values.yaml` |
| Capability dropping | All Linux capabilities dropped | `helm/webhook-service/values.yaml` |
| No default service account | OPA policy denies pods using "default" SA | `policies/pci_compliance.rego` |

## Requirement 3: Protect Stored Account Data

| Control | Implementation | Evidence |
|---------|---------------|----------|
| Encryption at rest (K8s secrets) | KMS key encrypts all K8s secrets | `terraform/modules/eks/main.tf` |
| Encryption at rest (EBS) | Node volumes encrypted with KMS | `terraform/modules/eks/main.tf` |
| Encryption at rest (ECR) | Container images encrypted with KMS | `terraform/modules/ecr/main.tf` |
| No hostPath volumes | OPA policy denies hostPath (unencrypted) | `policies/pci_compliance.rego` |
| Input validation | Pydantic v2 validates all transaction data | `services/webhook-service/models.py` |

## Requirement 6: Develop and Maintain Secure Systems and Software

| Control | Implementation | Evidence |
|---------|---------------|----------|
| Dependency scanning | Trivy scans container images and Python deps | `.github/workflows/ci-security.yml` |
| Static analysis (IaC) | Checkov + tfsec scan Terraform for misconfigs | `.github/workflows/ci-security.yml` |
| Secret scanning | Gitleaks scans full git history | `.github/workflows/ci-security.yml` |
| Automated testing | Pytest quality gate runs before security gates | `.github/workflows/ci-quality.yml` |
| Immutable artifacts | ECR image_tag_mutability = IMMUTABLE | `terraform/modules/ecr/main.tf` |
| Liveness/readiness probes | OPA policy requires both probes on all containers | `policies/pci_compliance.rego` |
| Version pinning | All dependencies pinned in requirements.txt | `services/webhook-service/requirements.txt` |

## Requirement 7: Restrict Access to System Components

| Control | Implementation | Evidence |
|---------|---------------|----------|
| Pod-level IAM (IRSA) | Each service gets dedicated IAM role via OIDC | `terraform/modules/eks/main.tf` |
| Dedicated service accounts | OPA denies "default" SA usage | `policies/pci_compliance.rego` |
| No cluster-admin binding | OPA denies ClusterRoleBinding to cluster-admin | `policies/pci_compliance.rego` |
| No privilege escalation | Container securityContext blocks escalation | `helm/webhook-service/values.yaml` |
| No privileged containers | OPA denies privileged: true | `policies/container_security.rego` |

## Requirement 8: Identify and Authenticate Access

| Control | Implementation | Evidence |
|---------|---------------|----------|
| IRSA-based identity | Pods authenticate to AWS via OIDC, not shared credentials | `terraform/modules/eks/main.tf` |
| Named service accounts | Each deployment uses a dedicated, named SA | `helm/webhook-service/templates/serviceaccount.yaml` |
| API authentication ready | Webhook service supports API key header validation | `services/webhook-service/config.py` |

## Requirement 10: Log and Monitor All Access

| Control | Implementation | Evidence |
|---------|---------------|----------|
| VPC Flow Logs | All network traffic logged to CloudWatch | `terraform/modules/vpc/main.tf` |
| EKS control plane logs | API, audit, authenticator, controller, scheduler | `terraform/modules/eks/main.tf` |
| Structured application logs | JSON-formatted logs with timestamp, level, module | `services/webhook-service/main.py` |
| Prometheus metrics | Request counts, latency histograms, transaction status | `services/webhook-service/main.py` |
| Audit labels | OPA requires `part-of` and `managed-by` labels on all pods | `policies/pci_compliance.rego` |
| Compliance reporting | Automated weekly sweep generates HTML/JSON reports | `scripts/compliance_reporter.py` |

## Requirement 11: Test Security of Systems and Networks Regularly

| Control | Implementation | Evidence |
|---------|---------------|----------|
| Automated vulnerability scanning | Trivy runs on every push (container + deps) | `.github/workflows/ci-security.yml` |
| ECR scan-on-push | Every pushed image automatically scanned | `terraform/modules/ecr/main.tf` |
| Weekly compliance sweep | Scheduled GitHub Actions job runs all scanners | `scripts/compliance_reporter.py` |
| Policy unit tests | OPA tests verify policies catch real violations | `policies/tests/` |
| API integration tests | Pytest validates webhook logic on every push | `.github/workflows/ci-quality.yml` |

## Supply Chain Security (Beyond PCI-DSS)

| Control | Implementation | Evidence |
|---------|---------------|----------|
| Container signing | cosign keyless signing via Sigstore | `.github/workflows/ci-security.yml` |
| Build provenance | SLSA Level 3 attestation on every production build | `.github/workflows/ci-security.yml` |
| Immutable tags | ECR prevents tag overwriting | `terraform/modules/ecr/main.tf` |
| Image lifecycle | ECR prunes untagged images after 1 day, keeps last 20 tagged | `terraform/modules/ecr/main.tf` |
