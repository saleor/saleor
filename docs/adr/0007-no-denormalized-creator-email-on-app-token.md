# AppToken does not denormalize the creator's email

**Tags:** apps, audit, permissions, data-minimization

`AppToken` records its creator only as a foreign key (`created_by`, `SET_NULL`).
We deliberately **do not** store a denormalized `created_by_email` column.

## Decision

An email is user PII, and we cannot retain it indefinitely. A denormalized
`*_email` column that is preserved after the user is deleted leaves orphaned PII
on the token forever, which conflicts with the `AGENTS.md` **Data minimization**
rule ("Don't denormalize user PII … ensure PII is deleted with the user"). So the
token holds only the reference id; when the creating user is deleted the FK goes
null and the token no longer resolves a creator.

This intentionally differs from the older `GiftCard.created_by_email` /
`AppProblem.dismissed_by_user_email` fields, which predate this decision and are
not the pattern to copy for new work.

## Consequence

- Durable "who created this token" attribution that must outlive the user is
  **not** solved by denormalizing PII onto `AppToken`. It will be handled by a
  dedicated audit-trail mechanism that persists that information in a compliant,
  retention-aware way.
- Until such an audit trail exists, creator information is best-effort: it is
  accurate while the user exists and becomes null once the user is deleted.
