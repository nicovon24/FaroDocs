# Identity, chat history, and provider credentials

Status: proposed design for account identity and durable credentials. The local fixed-owner preview now stores conversations and messages and accepts a request-only Groq key. No authentication, account-scoped history, or credential storage has been implemented or evaluated.

## Sign-in boundary

1. The browser starts Google OpenID Connect sign-in through a same-origin FaroDocs route. The backend uses the authorization code flow and validates the returned `state`, token issuer, audience, expiry, and ID token signature.
2. FastAPI maps the verified Google `sub` claim to a local User record. Email and display name may change and never act as the authorization key. Only `openid email profile` are requested for sign-in.
3. FastAPI creates an opaque, revocable application session. The browser receives a host-scoped HttpOnly, Secure, SameSite cookie in an HTTPS environment. Local HTTP development needs an explicit localhost-only cookie policy. The browser never stores a Google token or app session in localStorage.
4. Next.js reads the session to render protected screens. FastAPI checks the session and document grants on every domain request. Logout revokes the application session. Google Drive import, if added, asks for its own scopes in a separate consent flow.

## Durable user data

PostgreSQL holds User, Session, Conversation, Message, and Citation records. Conversations belong to a user and workspace. Messages record language, model/provider ID, time, and citation IDs for reproducibility. Opening history or a citation rechecks current document access; revoking access does not leave a backdoor through saved chats. The user can remove conversations. Account deletion must remove chats and credential records and follow a documented policy for files, audit metadata, backups, and external provider retention.

## User-selected AI provider

The settings screen lists supported providers and compatible model IDs, accepts a provider API key, tests it without retaining a raw copy in logs, and displays only a masked connection status afterward. The key is encrypted before persistence. The encryption key lives outside PostgreSQL and outside the repository, with a documented rotation and restore procedure. Only server-side code can decrypt for an authorized request. A user can replace or delete their connection; no endpoint returns the stored secret. Provider URLs are from an allowlist to avoid turning user settings into arbitrary server-side requests.

Generation receives bounded passages from documents the user can currently access. The UI explains that those passages leave FaroDocs for the selected external provider. Embeddings can run locally, so generating a search index does not require a provider key. Exact providers, models, cipher/key-management mechanism, retention policy, and hosting arrangement remain implementation decisions. A deterministic fake provider supports tests and local review without paid credits.

## Required checks before multi-user use

- Mocked Google callback rejects bad state, audience, signature, expiry, and replay; an opt-in live check is reported separately.
- Two users cannot read or alter each other's conversations, settings, ciphertext, or source previews.
- Logout invalidates the session; saved history and provider selection survive a new sign-in by the same Google account.
- API responses, browser storage, logs, traces, errors, and exports contain no raw provider key.
- Key replacement, revocation, and account deletion remove or disable the correct credential without affecting another user.

References: [Google OpenID Connect server flow](https://developers.google.com/identity/openid-connect/openid-connect), [OWASP session management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html), [OWASP secrets management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html).
