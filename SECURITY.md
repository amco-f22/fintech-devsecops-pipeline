# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it responsibly.

**Email:** amannikhare@protonmail.com

**Do not** open public GitHub issues for security concerns. You will receive a response within 48 hours.

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.x     | ✅         |

## Security Practices

This project implements the following security controls:

- **Secret scanning** — Gitleaks runs on every push
- **Container scanning** — Trivy scans images for CVEs
- **IaC scanning** — Checkov validates Terraform
- **Policy-as-code** — OPA/Rego admission policies
- **Supply chain** — cosign signing + SLSA L3 provenance
- **Dependency updates** — Dependabot monitors Terraform and GitHub Actions
