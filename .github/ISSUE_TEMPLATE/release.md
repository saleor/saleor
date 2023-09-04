---
name: New release
about: Template for issues to track Saleor releases
title: "Release <X.Y.Z>"
labels: release
assignees: ""
---

This issue tracks the release progress of Saleor <X.Y.Z>.

The release coordinator(s) for this version: <name> & <name>

## Steps

- [ ] Confirm scope related to Apps is ready to be released - @saleor/appstore
- [ ] Release alpha tag - @saleor/core
- [ ] Inform about the alpha tag - @saleor/core
- [ ] Release alpha tag - @saleor/dashboard
- [ ] Inform about the alpha tag - @saleor/dashboard
- [ ] Prepare environments for the new minor and trigger deployments - @saleor/cloud
- [ ] Inform about finished deployment - @saleor/cloud
- [ ] Add new snapshot for the newest version - @saleor/qa
- [ ] Perform alpha tests migration on staging - @saleor/qa
- [ ] Cypress tests review - @saleor/qa
- [ ] Check the change log and do smoke tests - @saleor/qa
- [ ] Inform the team about the results of the tests - @saleor/qa
- [ ] Perform smoke check on demo and storefront - @saleor/qa
- [ ] Inform about finished tests - @saleor/qa
- [ ] Release stable tag - @saleor/core
- [ ] Release stable tag  - @saleor/dashboard
- [ ] Accepts release PR to the sandbox - @saleor/qa
- [ ] Inform about approved release PR to the sandbox  - @saleor/qa
- [ ] Merge release PR to the sandbox - @saleor/cloud
- [ ] Merge release PR to the production - @saleor/cloud
- [ ] Inform about the stable release (sandbox and production) - @saleor/core
- [ ] Make the new version public in Saleor Cloud - @saleor/cloud
- [ ] Bump saleor-platform
- [ ] Merge docs PRs related to release - @saleor/devtools
