---
title: Contributing
---

> [!IMPORTANT]
> We value your contributions to Saleor and want to ensure they meet our project's needs. To help us maintain quality and consistency, we ask that you follow the process described in our [Contribution Guidelines](http://docs.saleor.io/developer/community/contributing). We welcome issues, new features, documentation improvements, community support, and more.

## Table of Contents

- [Running Saleor locally](#running-saleor-locally)
- [Managing dependencies](#managing-dependencies)
- [File structure](#file-structure)
- [Testing](#testing)
- [Coding style](#coding-style)
- [Tips and recommendation](#tips-and-recommendation)
- [Git commit messages](#git-commit-messages)
- [Pull requests](#pull-requests)
- [Changelog](#changelog)

## Running Saleor locally

### Running Saleor locally in development containers

The easiest way of running Saleor for local development is to use [development containers](https://containers.dev/).

Editor instructions:

- [Visual Studio Code](https://code.visualstudio.com/docs/devcontainers/containers#_quick-start-open-an-existing-folder-in-a-container)

- [PyCharm](https://www.jetbrains.com/help/pycharm/connect-to-devcontainer.html)

- [Codespaces](https://docs.github.com/en/codespaces/setting-up-your-project-for-codespaces/adding-a-dev-container-configuration/introduction-to-dev-containers)

Development container only creates container, you still need to start the server. See [common-commands](#common-commands) section to learn more.

### Running Saleor locally with database and additional services in docker

Install & setup prerequisites via homebrew:

```shell
brew install libmagic
brew install pyenv

pyenv install 3.12

# optionally set python globally
pyenv global 3.12

brew install pipx
pipx install poetry
```

Clone this [repository](https://github.com/saleor/saleor) and setup database and additional services in docker:

```shell
cd .devcontainer
docker compose up db dashboard redis mailpit
```

If you didn't set python version globally set [pyenv](https://github.com/pyenv/pyenv) local version:

```shell
pyenv local 3.12
```

To create virtualenv and install dependencies run in root of the repository:

```shell
poetry sync
```

After installation activate virtualenv:

```shell
eval $(poetry env activate)
```

See [poetry docs](https://python-poetry.org/docs/managing-environments/#bash-csh-zsh) for all supported shells.

> [!TIP]
> Your shell prompt should have virtualenv information available and should look similar to this:
> `(saleor-py3.12) ~/D/saleor %`

Install pre commit hooks:

```shell
pre-commit install
```

Create environment variables, by creating a `.env` file. You can use existing example for development:

```shell
cp .env.example .env
```

> [!NOTE]
> Example env variables set-up Celery broker, mail server, allow `localhost` URLs and set Dashboard URL
> so that your development setup works with additional services set-up via `docker compose`
>
> Learn more about each env variable in [Environment Variable docs](https://docs.saleor.io/setup/configuration)

> [!TIP]
> Env variables from `.env` file are loaded automatically by [Poe the Poet](https://poethepoet.natn.io/index.html) (when using `poe` commands below)

You are ready to go 🎉.

### Common commands

To start server:

```shell
poe start
```

to start Celery worker:

```
poe worker
```

to start Celery Beat scheduler:

```shell
poe scheduler
```

> [!NOTE]
> To learn more about Celery tasks and scheduler, check [Task Queue docs](https://docs.saleor.io/developer/running-saleor/task-queue#periodic-tasks)

To run database migrations:

```shell
poe migrate
```

To populate database with example data and create the admin user:

```shell
poe populatedb
```

> [!NOTE]
> `populatedb` populates database with example data and creates an admin account for `admin@example.com` with the password set to `admin`.*

To build `schema.graphql` file:

```shell
poe build-schema
```

To run Django shell:

```
poe shell
```

## Managing dependencies

### Poetry

To guarantee repeatable installations, all project dependencies are managed using [Poetry](https://python-poetry.org). The project's direct dependencies are listed in `pyproject.toml`.
Running `poetry lock` generates `poetry.lock` which has all versions pinned.

You can install Poetry by following the official installation [guide](https://python-poetry.org/docs/#installation).
We recommend using at least version `2.1.1` as it contains many fixes and features that Saleor relies on.

> [!TIP]
> We recommend using this workflow and keeping `pyproject.toml` and `poetry.lock` under version control to ensure that all computers and environments run the same code.

## File structure

We are using a standard Django structure - every app has its directory, where you can find:

- migrations directory
- management directory
- models
- utils - that keeps some functions of general utility related to this module
- error codes - the definitions of errors that might have appeared
- tests directory - that contains related tests, etc.

### API file structure

The `API` files are in `saleor/graphql/` directory. Every app has its directory
inside with:

- `schema.py` - with definitions of queries and mutations
- `sorters.py` - with definitions of sorters
- `filters.py` - with definitions of filters
- `types.py` - with definitions of corresponding types
- `enums.py` - with related enums
- `dataloaders.py` - with data loaders for the given module
- mutations file or directory
- tests directory

We aim to have a `mutations` directory in every module with a file per every mutation, as in the `checkout` directory. See the example below:

```bash
.
└── saleor
    └── graphql
        └── checkout
            ├── mutations
            │   └── checkout_create.py
            │   └── checkout_complete.py
            └── schema.py
```

### Tests file structure

We keep tests in the `tests` directory. We want to keep queries and mutations in separate directories with a single file for every query and mutation.
After joining it with the previous example, it would look like this:

```bash
.
└── saleor
    └── graphql
        └── checkout
            ├── mutations
            │   └── checkout_create.py
            │   └── checkout_complete.py
            ├── schema.py
            └── tests
                ├── mutations
                │   ├── test_checkout_complete.py
                │   └── test_checkout_create.py
                └── queries
                    └── test_checkout.py
                    └── test_checkouts.py
```

## Testing

Testing is an essential part of every project.
In Saleor, we use the `pytest` library and mostly have unit tests.

To reduce tests execution time, we use [pytest-xdist](https://pypi.org/project/pytest-xdist/)
that allows running tests on more than one CPU. By default, we use `-n=auto`, which creates a separate process equal to the number of available CPUs.

We are also using [pytest-socket](https://pypi.org/project/pytest-socket/)
to ensure that our tests do not hit any external API without explicitly allowing this.

The test file structure was introduced in the [tests file structure](./contributing#tests-file-structure).
The main rule is not to overload test files. Smaller files are always preferable over big ones where lots of logic is tested, and it's hard to extend.
In the case of testing the `API`, we would like to split all tests into `mutations` and `queries` sections and test every query and mutation in a separate file.

### How to run tests?

To run tests, enter `poe test` in your terminal.

```bash
poe test
```

By default `poe test` is using the `--reuse-db` flag to speed up testing time.

> [!TIP]
> If you need to ignore `--reuse-db` (e.g when testing Saleor on different versions that have different migrations) add `--create-db` argument: `poe test --create-db`

### How to run particular tests?

As running all tests is quite time-consuming, sometimes you want to run only tests from one dictionary or even just a particular test.
You can use the following command for that. In the case of a particular directory or file, provide the path after the `pytest` command, like:

```bash
poe test saleor/graphql/app/tests
```

If you want to run a particular test, you need to provide the path to the file where the test is and the file name after the `::` sign. In the case of running a single test, it's also worth using the `-n0` flag to run the test only in one thread. It will significantly decrease time.
See an example below:

```bash
poe test saleor/graphql/app/tests/mutations/test_app_create.py::test_app_create_mutation -n0
```

### Using pdb when testing

If you would like to use `pdb` in code when running a test, you need to use a few flags `-n0` to one test in a single thread, `-s` to disable capturing standard output by pytest, and `--allow-hosts` with a default port, as we disabled sockets by default.
So the previous example will look like this:

```bash
poe test saleor/graphql/app/tests/mutations/test_app_create.py::test_app_create_mutation -n0 -s --allow-hosts=127.0.0.1
```

### Recording cassettes

Some of our tests use `VCR.py` cassettes to record requests and responses from external APIs. To record one, you need to use the `vcr-record` flag and specify `allow-hosts`:

```bash
poe test --vcr-record=once saleor/app/tests/test_app_commands.py --allow-hosts=127.0.0.1
```

### Writing benchmark tests

The benchmark tests allow us to keep track of several database queries for mutations and queries. Tests should be added for every new
mutation or query for objects.
The benchmark tests are in `benchmark` directory, every test must be marked with `pytest.mark.django_db` and `pytest.mark.count_queries(autouse=False)` decorators and must have `count_queries` argument. For more details, check
[pytest-django-queries](https://pypi.org/project/pytest-django-queries/) package.

```python
@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_apps_for_federation_query_count(
    staff_api_client,
    permission_manage_apps,
    django_assert_num_queries,
    count_queries,
):
    ...
```

To check the number of queries, run the benchmark test, and after that, call the following command in your terminal:

```bash
django-queries show
```

You will see the number of queries that were performed for each test
in every file.

### Given, when, then

We recommend using `given`, `when`, `then` to distinguish between different test parts.
It significantly improves test readability and clarifies what you are testing.

## Coding style

Saleor uses various tools to maintain a common coding style and help with development.
To install all the development tools, use [Poetry](https://python-poetry.org):

```shell
poetry sync
```

Saleor uses the [pre-commit](https://pre-commit.com/#install) tool to check and automatically fix any formatting issue before creating a git commit.

Run the following command to install pre-commit into your git hooks and have it run on every commit:

```shell
pre-commit install
```

For more information on how it works, see the `.pre-commit-config.yaml` configuration file.

> [!NOTE]
> Running `git commit` for the first time might take a while, since all dependencies will be setting up.

Saleor has a strict formatting policy enforced by the [black formatting tool](https://github.com/python/black).

Module names should make their purpose obvious. Avoid generic file names such as `utils.py`.

### Linters

Use [ruff](https://github.com/astral-sh/ruff) to check and format your code.

### EditorConfig

[EditorConfig](http://editorconfig.org/) is a standard configuration file that aims to ensure consistent style across multiple programming environments.

Saleor's repository contains [an `.editorconfig` file](.editorconfig) describing our formatting requirements.

Most editors and IDEs support this file either directly or via plugins. See the [list of supported editors and IDEs](http://editorconfig.org/#download) for detailed instructions.

If you make sure that your programming environment respects the contents of this file, you will automatically get correct indentation, encoding, and line endings.

## Tips and recommendation

Here are some tips and recommendations for limiting the number of comments to your PR.
If you follow those rules, both sides will be happy.

### Imports

Use relative imports.

### Models

- The `UUID` is the preferred type of `PK` for the main models, especially for models that
  keep sensitive data.
- Use `created_at` field name for creation date time and `updated_at` for update date time.
- The new models should have a default sorting value set. It ensures that data is always returned in the same order and prevent flaky tests.

### Migrations

Try to combine multiple migrations into one, but remember not to mix changes on the database with updating rows in migrations. In other words, operations that alter tables and use `RunPython` to run methods on existing data should be in separate files.
Follow [zero-downtime policy](./developer/community/zero-downtime-migrations.mdx) when writing migrations.

### Handling migrations between versions

If you need to add the migration to the module that has different migrations on different versions,
you need to start from the lower version (let's say 3.1) and make the changes that you want to apply there.

Then you need to move to the upper version (in our case it will be 3.2), cherry-pick the newly added
migration (on the 3.1 version), and create a migration merge if needed with the use of
`./manage.py makemigrations --merge`. Follow these steps on all versions and on the main branch.

### Reversible migrations

We should keep all migrations reversible. Each time you add new migrations,
especially custom ones with `RunPython` and `RunSQL` operations, ensure that
you define the `reverse` option. The easiest option and enough for most cases is just
using `migrations.RunPython.noop`.

### Utility functions

Utility functions specific to the API should go to the `graphql` directory,
otherwise to the main module directory, usually to the `utils.py` file.
Try to find a name as descriptive as possible when writing such a method.
Also, do not forget about the docstring, especially in a complicated function.

### Searching

So far, we have mainly used the `GinIndex` and `ilike` operators for searching, but currently, we are testing a new solution with the use of `SearchVector` and `SearchRank`.
You can find it in this PR [#9344](https://github.com/saleor/saleor/pull/9344).

> [!NOTE]
> The search vector update task is triggered by [celery beat scheduler](https://docs.saleor.io/developer/running-saleor/task-queue#periodic-tasks).
> This feature will not work without task queue configuration.

### API

- Use `id` for mutation inputs instead of `model_name_id`.
- Use `created_at` field name for creation date time and `updated_at` for update date time.

#### API field descriptions

Every mutation, mutation field, and type field should have a short, meaningful description ending with a dot. Also, we labeled every new field with info in which version it was introduced, and when it's a new feature, we added the preview feature label.
The labels `ADDED_IN_X` and `PREVIEW_FEATURE` should be at the end of the description.
All labels can be found in `saleor/graphql/core/descriptions.py`.

When we want to remove the API field, we mark it first as `DEPRECATED`.
In a field definition, there is a dedicated argument for that: `deprecation_reason`, but for mutation arguments, we use `DEPRECATED_IN_X_INPUT` label in the description.

#### How to define permissions in queries/mutations?

To define permission in queries, use the `permission_required` decorator to provide one or multiple permissions that are required or the `one_of_permissions_required` decorator that allows a user with at least one permission to perform the action.

In the case of mutations, the permissions are defined in the `Meta` arguments in the `permissions` field.
To represent all permissions the same way, we introduced the `AuthorizationFilters` enum that represents permission checks that are based on functions instead of named admin permission scopes.
When raising `PermissionDenied`, the error should mention which permissions are required to perform the given action.

> [!NOTE]
> Required permissions should be mentioned in the GraphQL description.

#### Handling changes on API in PREVIEW_FEATURE

Applying changes on API fields with `PREVIEW_FEATURE` must be handled with the deprecation,
but the deprecated fields can be removed in the next `minor` version.
The changes must be mentioned in the `Braking changes` section of the changelog.

#### Error codes

New mutations should always have their error class.
Example: instead of using generic `PaymentErrorCode`, for `PaymentCreate` mutation we could have `PaymentCreateErrorCode`. The frontend will get a list of error codes that could be triggered by this mutation instead of the list of all errors that could be raised
by ALL payment mutations.

The error classes are defined in the `saleor/graphql/core/types/common.py` file.
You will need the GraphQL enum with error codes to create the new one.
First, create a new enum in the `error_codes.py` file in the main app directory.
Then use it to create a GraphQL enum in the `saleor/graphql/core/enums.py` file.
When defining a GraphQL enum, you could specify the enum type name and attach the description, for example, the enum docstring, as is shown below.

```python
AppTypeEnum = to_enum(
    AppType,
    type_name="AppTypeEnum",
    description=AppType.__doc__,
)
```

Now you are ready to define the error class. The class must inherit from `Error` and have a `code` field. All other fields are optional, but it could be helpful to specify what inputs raised an error. Here is an example:

```python
class AppError(Error):
    code = AppErrorCode(description="The error code.", required=True)
    permissions = NonNullList(
        PermissionEnum,
        description="List of permissions which causes the error.",
        required=False,
    )
```

#### Sorting and filtering

To allow sorting of the queryset, you must create the `SortInputObjectType` and corresponding sorting enum, and it should go to the dedicated `sorters.py` file in the given app module in the `API`.

```python
class AppSortField(graphene.Enum):
    NAME = ["name", "pk"]
    CREATION_DATE = ["created", "name", "pk"]

    @property
    def description(self):
        if self.name in AppSortField.__enum__._member_names_:
            sort_name = self.name.lower().replace("_", " ")
            return f"Sort apps by {sort_name}."
        raise ValueError("Unsupported enum value: %s" % self.value)


class AppSortingInput(SortInputObjectType):
    class Meta:
        sort_enum = AppSortField
        type_name = "apps"
```

> [!WARNING]
> Remember, the list with sorting order must have a unique field.

> [!TIP]
> Sometimes you would like to sort the data by some field that should be calculated, which isn't the model field. There is an option for that; you need to create a method whose name starts with `qs_with` followed by a sort field name in lowercase.
> The method should annotate the queryset to contain the new value. Look at the example:
>
> ```python
> class CollectionSortField(graphene.Enum):
>     NAME = ["name", "slug"]
>     PRODUCT_COUNT = ["product_count", "slug"]
>
>     @property
>     def description(self):
>         if self.name in CollectionSortField.__enum__._member_names_:
>             sort_name = self.name.lower().replace("_", " ")
>             return f"Sort collections by {sort_name}."
>         raise ValueError("Unsupported enum value: %s" % self.value)
>
>     @staticmethod
>     def qs_with_product_count(queryset: QuerySet, **_kwargs) -> QuerySet:
>         return queryset.annotate(product_count=Count("collectionproduct__id"))
>
> ```

A similar behavior can be found in filtering: you need to create `FilterInputObjectType`
and Django `FilterSet` in a dedicated `filters.py` file.

```python
class AppFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = AppFilter


class AppFilter(django_filters.FilterSet):
    type = EnumFilter(input_class=AppTypeEnum, method=filter_app_type)
    search = django_filters.CharFilter(method=filter_app_search)
    is_active = django_filters.BooleanFilter()

    class Meta:
        model = models.App
        fields = ["search", "is_active"]
```

Next, you need to create the `CountableConnection` for a given query:

```python
class AppCountableConnection(CountableConnection):
    class Meta:
        node = App
```

Then in the `schema.py` file, you need to change the corresponding query.
It must be a `FilterConnectionField` with created connection field,
sorting input must be used in the `sort_by` argument, and filter input in the `filter` argument of the query:

```python
class AppQueries(graphene.ObjectType):
    apps = FilterConnectionField(
        AppCountableConnection,
        filter=AppFilterInput(description="Filtering options for apps."),
        sort_by=AppSortingInput(description="Sort apps."),
        description="List of the apps.",
    )
```

#### How to handle breaking changes?

- provide a compatibility layer by supporting two solutions for a specified time period and removing them in the next major version
- deprecate API fields instead of removing them

### Optimization

To check if your solution is well-optimized, you can visualize the execution plan for
the performed SQL statements.

> [!NOTE]
> To reliably check the performance, it should be tested on at least 1000 instances.

Below you find a step-by-step guide on how to do this with the use of [explain](https://explain.dalibo.com/).

1. In the first step you need to add `debug` to the GraphQL queries and mutations.
   To do this, follow the steps that are described [here](https://docs.graphene-python.org/projects/django/en/latest/debug/#installation).
   Extend the `Mutation` object type in the same way as the `Query` object type is extended.
2. Extend the query that you want to measure with the `_debug` part:

```graphql
_debug {
    sql {
      rawSql
    }
  }
```

You can find an example [here](https://docs.graphene-python.org/projects/django/en/latest/debug/#querying).

3. Next, choose the statement that you want to visualize from the data that you received.
4. Create the `.sql` file (e.x. `data.sql`) with `EXPLAIN (ANALYZE, COSTS, VERBOSE, BUFFERS, FORMAT JSON)`
   followed by a chosen statement.
5. Run the command below in your terminal in the localization of the previously created file.

```bash
psql -h <host-name> -p <db-port> -U <db-user> -XqAt -f data.sql > analyze.json
```

It should look similar to:

```bash
psql -h localhost -p 5432 -U saleor -XqAt -f data.sql > analyze.json
```

6. Open the `analyze.json`, copy the data and paste it to the `plan` input field in [explain.dalibo](https://explain.dalibo.com/).
   Add an optional corresponding SQL query if you wish.
7. Press the `Submit` button and that's it. You can analyze what you get.

### Debugging

We recommend you use `breakpoint()` function to set debugger. If you are using devcontainer `breakpoint` will use [ipdb](https://pypi.org/project/ipdb/). To learn more about `breakpoint` see official [PEP 553](https://peps.python.org/pep-0553/).

## Git commit messages

To speed up the review process and to keep the logs tidy, we recommend the following simple rules on how to write good commit messages:

### Summary line

- It should contain less than 50 characters. It is best to make it short
- Introduce what has changed, using imperatives: fix, add, modify, etc.

### Description

- Add extra explanation if you feel it will help others to understand the summary content
- If you want, use bullet points (each bullet beginning with a hyphen or an asterisk)
- Avoid writing in one line. Use line breaks so the reader does not have to scroll horizontally

> [!TIP]
> To ease review, try to limit your commits to a single, self-contained issue. This will also help others to understand and manage them in the future.

For more information and tips on how to write good commit messages, see the GitHub [guide](https://github.com/erlang/otp/wiki/writing-good-commit-messages).

## Pull requests

Remember to add a meaningful title and a good description when you open a pull request.
Please describe what is changing, the reason for doing that, or what problem it fixes.
All Pull Requests should be linked to their corresponding GitHub issues.

## Changelog

We have a `CHANGELOG.md` file where we keep the info about the introduced changes.
The file contains separate parts for every release. You should put each new item under the `Unreleased` section.
This section is split into `Breaking changes` and `Other changes`.
The changelog entry should consist of the name of the PR, the PR number, and the author's name. It may also contain an additional explanation. Here is an example:

```
- Add multichannel - #6242 by @exampleUser
```

### What is considered a breaking change?

Here is a complete list of changes that we consider breaking:

- deleting a field from the GraphQL schema / renaming the field name
- deleting the field from the webhook payload / changing the name of the returned field
- changing signatures of plugins functions (PluginsManager) - breaking only for existing plugins
- adding new validation in a mutation logic - it may break storefronts and apps
- changing of the API behavior even if the schema doesn't change - e.g., the type of field hasn't changed, but the requirements for value has

Any change that is not specified there should go to the `Other changes` section.

### I'm adding a fix to a just-merged feature. Should I add a changelog record for that?

The changelog shouldn't reflect the history of building a feature, but it should provide the information for other developers that an actual feature was added.
If the feature wasn't released, and you believe the PR number of the fix is worth mentioning, the existing changelog entry should be extended:

```
- Add multichannel - #6242, #6250 by @exampleUser
```

If the fix is not crucial, it shouldn't be mentioned separately.

If a feature was released, you could add a separate changelog entry to mention a regular bug fix.
