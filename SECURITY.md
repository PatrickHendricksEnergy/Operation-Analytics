# Security

## Secrets Management
- Never commit `.env` or API keys.
- Use environment variables for credentials (e.g., `OPENAI_API_KEY`).
- Rotate keys if exposure is suspected.

## Data Access
- Limit access to raw data to authorized users.
- Store exports and reports only in approved locations.

## Reproducibility
- Use the pinned `requirements.txt` to recreate the environment.
- Record any additional dependencies or system requirements.

## Incident Response
- If a secret or sensitive data is exposed, revoke access immediately and notify stakeholders.
