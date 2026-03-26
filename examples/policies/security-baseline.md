# Security baseline (example policy for RAG indexing)

Use this folder as a sample corpus. Replace with your org standards (SOC2 excerpts, internal threat models, Terraform baselines).

## Secrets

- Never commit API keys, tokens, or private keys. Use a secret manager or CI-injected variables.
- Rotate credentials when exposure is suspected.

## Containers

- Run application processes as non-root where possible.
- Pin base image digests in production pipelines.

## Infrastructure

- Deny overly broad IAM (`Action: "*"`, `Resource: "*"` with writes).
- Encrypt data at rest for databases and object storage used for sensitive data.
