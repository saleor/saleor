from .....app.models import AppProblem, AppProblemSeverity, AppProblemType
from ....tests.utils import assert_no_permission, get_graphql_content

APP_PROBLEM_CREATE_MUTATION = """
    mutation AppProblemCreate($input: AppProblemCreateInput!) {
        appProblemCreate(input: $input) {
            app {
                id
                problems {
                    ... on AppProblemOwn {
                        message
                        aggregate
                        severity
                        key
                    }
                }
            }
            errors {
                field
                code
                message
            }
        }
    }
"""


def test_app_problem_create(app_api_client, app):
    # given
    variables = {"input": {"message": "Something went wrong"}}

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_CREATE_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemCreate"]
    assert not data["errors"]
    problems = data["app"]["problems"]
    assert len(problems) == 1
    assert problems[0]["message"] == "Something went wrong"
    assert problems[0]["aggregate"] == ""
    assert problems[0]["severity"] == "ERROR"

    db_problem = AppProblem.objects.get(app=app)
    assert db_problem.type == AppProblemType.OWN
    assert db_problem.message == "Something went wrong"
    assert db_problem.severity == AppProblemSeverity.ERROR


def test_app_problem_create_with_aggregate(app_api_client, app):
    # given
    variables = {"input": {"message": "Connection failed", "aggregate": "webhook-123"}}

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_CREATE_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemCreate"]
    assert not data["errors"]
    problems = data["app"]["problems"]
    assert len(problems) == 1
    assert problems[0]["message"] == "Connection failed"
    assert problems[0]["aggregate"] == "webhook-123"

    db_problem = AppProblem.objects.get(app=app)
    assert db_problem.aggregate == "webhook-123"


def test_app_problem_create_with_warning_severity(app_api_client, app):
    # given
    variables = {"input": {"message": "Degraded performance", "severity": "WARNING"}}

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_CREATE_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemCreate"]
    assert not data["errors"]
    problems = data["app"]["problems"]
    assert len(problems) == 1
    assert problems[0]["message"] == "Degraded performance"
    assert problems[0]["severity"] == "WARNING"

    db_problem = AppProblem.objects.get(app=app)
    assert db_problem.severity == AppProblemSeverity.WARNING


def test_app_problem_create_with_error_severity(app_api_client, app):
    # given
    variables = {"input": {"message": "Fatal failure", "severity": "ERROR"}}

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_CREATE_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemCreate"]
    assert not data["errors"]
    problems = data["app"]["problems"]
    assert len(problems) == 1
    assert problems[0]["severity"] == "ERROR"

    db_problem = AppProblem.objects.get(app=app)
    assert db_problem.severity == AppProblemSeverity.ERROR


def test_app_problem_create_by_staff_user_fails(
    staff_api_client, permission_manage_apps
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_apps)
    variables = {"input": {"message": "Something went wrong"}}

    # when
    response = staff_api_client.post_graphql(APP_PROBLEM_CREATE_MUTATION, variables)

    # then
    assert_no_permission(response)


def test_app_problem_create_multiple(app_api_client, app):
    # given
    AppProblem.objects.create(
        app=app,
        type=AppProblemType.OWN,
        message="Existing problem",
    )
    variables = {"input": {"message": "New problem"}}

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_CREATE_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemCreate"]
    assert not data["errors"]
    assert AppProblem.objects.filter(app=app).count() == 2


def test_app_problem_create_fails_when_limit_reached(app_api_client, app):
    # given
    AppProblem.objects.bulk_create(
        [
            AppProblem(
                app=app,
                type=AppProblemType.OWN,
                message=f"Problem {i}",
            )
            for i in range(AppProblem.MAX_PROBLEMS_PER_APP)
        ]
    )
    variables = {"input": {"message": "One too many"}}

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_CREATE_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemCreate"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["code"] == "INVALID"
    assert data["app"] is None
    assert AppProblem.objects.filter(app=app).count() == AppProblem.MAX_PROBLEMS_PER_APP


def test_app_problem_create_with_key(app_api_client, app):
    # given
    variables = {"input": {"message": "Keyed problem", "key": "my-key"}}

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_CREATE_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemCreate"]
    assert not data["errors"]
    problems = data["app"]["problems"]
    assert len(problems) == 1
    assert problems[0]["message"] == "Keyed problem"
    assert problems[0]["key"] == "my-key"

    db_problem = AppProblem.objects.get(app=app)
    assert db_problem.key == "my-key"


def test_app_problem_create_skips_duplicate_key(app_api_client, app):
    # given
    AppProblem.objects.create(
        app=app,
        type=AppProblemType.OWN,
        message="Original",
        key="dup-key",
    )
    variables = {"input": {"message": "Duplicate", "key": "dup-key"}}

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_CREATE_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemCreate"]
    assert not data["errors"]
    assert AppProblem.objects.filter(app=app).count() == 1
    assert AppProblem.objects.get(app=app).message == "Original"


def test_app_problem_create_force_overwrites_existing(app_api_client, app):
    # given
    original = AppProblem.objects.create(
        app=app,
        type=AppProblemType.OWN,
        message="Original",
        severity=AppProblemSeverity.WARNING,
        key="overwrite-key",
    )
    original_created_at = original.created_at
    variables = {
        "input": {
            "message": "Updated",
            "severity": "ERROR",
            "key": "overwrite-key",
            "force": True,
        }
    }

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_CREATE_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemCreate"]
    assert not data["errors"]
    assert AppProblem.objects.filter(app=app).count() == 1

    updated = AppProblem.objects.get(app=app)
    assert updated.pk == original.pk
    assert updated.message == "Updated"
    assert updated.severity == AppProblemSeverity.ERROR
    assert updated.created_at > original_created_at


def test_app_problem_create_different_keys_both_created(app_api_client, app):
    # given
    AppProblem.objects.create(
        app=app,
        type=AppProblemType.OWN,
        message="First",
        key="key-x",
    )
    variables = {"input": {"message": "Second", "key": "key-y"}}

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_CREATE_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemCreate"]
    assert not data["errors"]
    assert AppProblem.objects.filter(app=app).count() == 2
    assert AppProblem.objects.filter(app=app, key="key-x").exists()
    assert AppProblem.objects.filter(app=app, key="key-y").exists()


def test_app_problem_create_no_key_allows_duplicates(app_api_client, app):
    # given
    variables = {"input": {"message": "No key problem"}}
    app_api_client.post_graphql(APP_PROBLEM_CREATE_MUTATION, variables)

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_CREATE_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemCreate"]
    assert not data["errors"]
    assert AppProblem.objects.filter(app=app).count() == 2
