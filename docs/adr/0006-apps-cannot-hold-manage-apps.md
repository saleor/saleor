# Apps cannot hold MANAGE_APPS

**Tags:** apps, security, permissions

An App must **never** hold the `MANAGE_APPS` permission. This is enforced at grant
time by `ensure_app_permissions_allowed` (`saleor/graphql/app/utils.py`): any
attempt to assign `MANAGE_APPS` to an app is rejected with
`OUT_OF_SCOPE_PERMISSION` — **even for superusers**. Migration
`app/0039_remove_manage_apps_permission` stripped the permission from any apps
that held it before the rule existed.

The reasoning is to prevent privilege laundering through a non-human principal:
`MANAGE_APPS` lets a principal create tokens and manage other apps, so granting
it to an app would let an app escalate its own reach without a human in the loop.
Keeping it human-only means every app-management action is attributable to a
staff user.
