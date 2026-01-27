# High level goal

We will update module "saleor/app". Each "app" instance should have concept of "Problems".

You can find what "problem" is in saleor/checkout, which has similar concept implemented

Each app should be able to contain list of problems. Can have 0 or more.

Each problem should be a separate database model

When app is removed, all problems should be removed as well.

Problem can be added programatically or via graphql

programatically: when some events happen, problem can be added. For example, when Saleor disables app due to corcuit-breaker, Saleor should be abble to attach new problem to app.
via graphql: app can add new problem via graphql mutation on itself

## Problem types

In graphql there should be some base interface for problem and specific problems.

For example:

Base Problem:
- message
- date created

Specific problems (that extend base problem):
- CircuitBreakerProblem (when Saleor disables app due to circuit-breaker
- CustomProblem (when App sets problem on itself)

Each specific problem should have additional __typename__ field.

In the future we will add more problem types

## Graphql

we must be able to query app.problems (no pagination needed)

we must be able to attach new problem to app via graphql mutation (on self)

we must be able to clear problems: we must decide how to do it. We dont want to clear all, but also dont want to clear by ID. Best if CustomProblem has some "aggregate" field, for example

```
mutation appProblemAdd(..., aggregate: "my-custom-problem"){}

# run twice
mutation appProblemAdd(..., aggregate: "my-custom-problem"){}

# not related problem
mutation appProblemAdd(..., aggregate: "my-custom-problem-another"){}

# should clear only "my-custom-problem"
mutation appProblemClear(aggregate:"my-custom-problem")
```

Also we should be able to clear all CustomProblems (added by app), but not other problems.

## Database

You should design database model, but for sure:
1. App has relation to many problems
2. When app is deleted, problems should be cleared
3. Some problems may have custom fields, which other problems dont have

## Additional notes

You should design this feature, including API layer (graphql) and database model.
