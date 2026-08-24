# Contributing

Thank you for considering contributing to the Fintech DevSecOps Pipeline.

## How to Contribute

1. Fork the repository and create a feature branch from `main`.
2. Make your changes following the guidelines below.
3. Open a pull request describing the change and its security implications.

## Development Guidelines

### Terraform
- Run `terraform fmt` before committing
- Run `terraform validate` on modified modules
- Ensure Checkov produces no new HIGH/CRITICAL findings

### OPA/Rego Policies
- Write unit tests for every new `deny` rule in `policies/tests/`
- Run `opa test policies/ -v` to verify all tests pass

### FastAPI Service
- Run `pytest tests/ -v` and ensure all tests pass
- Add tests for new endpoints or business logic
- Pin new dependencies in `requirements.txt`

### Helm Chart
- Run `helm lint helm/webhook-service/` before committing
- Run `helm template test helm/webhook-service/` to verify rendering

## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add transaction retry logic
fix: correct idempotency check for duplicate webhook
chore: update Terraform provider to 5.x
security: add OPA rule for hostNetwork denial
```

## Security Issues

Please do **not** open public issues for security vulnerabilities. See [SECURITY.md](SECURITY.md) for responsible disclosure instructions.
