# Accepted risks for storefront traffic blocking

**Tags:** graphql, security, storefront, oidc

Merchants can disable direct **storefront traffic** to the GraphQL API so only
staff users and apps are allowed to call the API directly. This is intended as a
way to limit public traffic-control.

The feature deliberately accepts a few risks to keep the implementation simple.

## Risk: cache evictions & replica delays

The enforcement decision uses a short-lived cache for `allow_storefront_traffic`.
On cache miss, the setting may be read from a DB replica which can mean a recent
setting change can cause public traffic to be allowed while it should have been
blcked instead.

This is accepted because the setting taking time to propagate doesn't pose any
real impact to merchants. This is an unrealistic risk and therefore shouldn't
accounted for.

This includes:
- Cache evictions due to high memory pressure
- Cache expiration (TTL exceeded)
- Replication lag (miliseconds to multiple seconds)

## Risk: rejection happens after request parsing and validation

Blocked anonymous or customer traffic is rejected after parsing the body and
after performing some other preparations to process the request, including
running user-input validations (such as query cost).

This means unauthenticated traffic hitting the HTTP workers while the storefront
traffic is disabled requires considerable resources to process the requests prior
to returning HTTP 401.

This is accepted because moving the check earlier would require significant changes
to the way Saleor handles HTTP requests without actually bringing any value to the
project.

The feature is only intended to be used for restricting public access, and not
as way to guard against attacks; instead a WAF and other controls should be put
in place by the deployer.
