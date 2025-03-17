I want to merge this change because...

<!-- Please mention all relevant issue numbers. -->
<!-- GitHub issue number is required for external contributions. -->

# Impact

- [ ] New migrations
- [ ] New/Updated API fields or mutations
- [ ] Deprecated API fields or mutations
- [ ] Removed API types, fields, or mutations

# Docs

<!-- Docs are stored in a separate repository: https://github.com/saleor/saleor-docs/. -->
<!-- Please provide a link to the PR that updates documentation for your changes. -->
<!-- If changes in docs are not required, please mention that in the description. -->

- [ ] Link to documentation:

# Pull Request Checklist

<!-- Please keep this section. It will make the maintainer's life easier. -->

- [ ] Privileged queries and mutations are either absent or guarded by proper permission checks
- [ ] Database queries are optimized and the number of queries is constant
- [ ] Database migrations are either absent or optimized for zero downtime
- [ ] The changes are covered by test cases
- [ ] All new fields/inputs/mutations have proper labels added (`ADDED_IN_X`, `PREVIEW_FEATURE`, etc.)
- [ ] All migrations have proper dependencies
- [ ] All indexes are added concurrently in migrations
- [ ] All RunSql and RunPython migrations have revert option defined
