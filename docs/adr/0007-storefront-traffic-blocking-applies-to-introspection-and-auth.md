# Storefront traffic blocking applies to introspection and authentication

**Tags:** graphql, security, storefront, oidc

When storefront traffic is disabled (`Shop.allowStorefrontTraffic = false`), the
guard runs in the GraphQL view before the document is executed and rejects every
non-privileged request with HTTP 401. It does not inspect the operation, so it
also rejects:

- **Introspection queries** — the schema is not readable without staff or app
  credentials.
- **Authentication operations** — `tokenCreate`, `tokenRefresh`,
  `externalObtainAccessTokens` and friends. A customer cannot obtain a token, so
  a customer can never become privileged enough to pass the guard.

This is by design. Exempting operations would mean parsing and classifying the
document before the check, adding an allowlist that must be kept in sync with
every new auth-related mutation, and leaving a public surface that defeats the
point of the setting.

The setting is intended for deployments that put a **proxy in front of the whole
API layer** — the proxy holds app or staff credentials (or terminates the
storefront's own auth) and is the only thing talking to Saleor directly. In that
topology introspection and login both happen through the proxy, so nothing needs
to be exempt.

Merchants that need public login or public introspection should not enable this
setting.

See also: [0006](0006-storefront-traffic-blocking-accepted-risks.md).
