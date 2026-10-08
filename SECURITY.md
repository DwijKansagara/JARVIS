# Security

Report suspected vulnerabilities privately to **kansagara.dwij@gmail.com**. Revoke an exposed provider key before reporting it.

The web edition is static and has no project backend or account system. A user-provided OpenRouter key remains in page memory only and is never written to local storage or session storage. Prompts go directly to OpenRouter after explicit consent. Model output is inserted with `textContent`, so provider text cannot create HTML. Conversation history is functional local storage and can be cleared with **New conversation** or browser site-data controls.

The desktop edition reads local keys from ignored configuration files. Never commit, log, upload, or bundle those files. The shared appreciation API uses exact origins, request-intent checks, parameterized SQL, durable rate limiting, salted identifiers, restricted database privileges, and server-held secrets.

This project currently has no passwords, JWTs, uploads, webhooks, public database client, or arbitrary server-side URL fetcher. Those features must pass the workspace security baseline before they are added. Production source maps and default credentials are forbidden. Enable MFA on GitHub, OpenRouter, hosting, and other privileged provider accounts.
