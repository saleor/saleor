import graphene

from .....app.models import AppProblem, AppProblemType
from ....tests.utils import assert_no_permission, get_graphql_content

APP_PROBLEM_CLEAR_MUTATION = """
    mutation AppProblemClear($app: ID, $aggregate: String, $key: String) {
        appProblemClear(app: $app, aggregate: $aggregate, key: $key) {
            app {
                id
                problems {
                    ... on AppProblemOwn {
                        message
                        aggregate
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


def test_app_problem_clear_all_custom(app_api_client, app):
    # given
    AppProblem.objects.create(app=app, type=AppProblemType.OWN, message="Problem 1")
    AppProblem.objects.create(
        app=app, type=AppProblemType.OWN, message="Problem 2", aggregate="group-a"
    )

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_CLEAR_MUTATION)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemClear"]
    assert not data["errors"]
    assert AppProblem.objects.filter(app=app).count() == 0


def test_app_problem_clear_by_aggregate(app_api_client, app):
    # given
    AppProblem.objects.create(
        app=app, type=AppProblemType.OWN, message="Problem 1", aggregate="group-a"
    )
    AppProblem.objects.create(
        app=app, type=AppProblemType.OWN, message="Problem 2", aggregate="group-b"
    )
    variables = {"aggregate": "group-a"}

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_CLEAR_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemClear"]
    assert not data["errors"]
    remaining = AppProblem.objects.filter(app=app)
    assert remaining.count() == 1
    assert remaining.first().aggregate == "group-b"


def test_app_problem_clear_by_staff_user_with_app_arg(
    staff_api_client, app, permission_manage_apps
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_apps)
    AppProblem.objects.create(app=app, type=AppProblemType.OWN, message="Problem 1")
    AppProblem.objects.create(app=app, type=AppProblemType.OWN, message="Problem 2")
    variables = {"app": graphene.Node.to_global_id("App", app.id)}

    # when
    response = staff_api_client.post_graphql(APP_PROBLEM_CLEAR_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemClear"]
    assert not data["errors"]
    assert AppProblem.objects.filter(app=app).count() == 0


def test_app_problem_clear_by_staff_without_permission(staff_api_client, app):
    # given
    variables = {"app": graphene.Node.to_global_id("App", app.id)}

    # when
    response = staff_api_client.post_graphql(APP_PROBLEM_CLEAR_MUTATION, variables)

    # then
    assert_no_permission(response)


def test_app_problem_clear_by_staff_without_app_arg(
    staff_api_client, permission_manage_apps
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_apps)

    # when
    response = staff_api_client.post_graphql(APP_PROBLEM_CLEAR_MUTATION)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemClear"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["field"] == "app"
    assert data["errors"][0]["code"] == "REQUIRED"


def test_app_problem_clear_app_caller_with_app_arg(app_api_client, app):
    # given
    variables = {"app": graphene.Node.to_global_id("App", app.id)}

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_CLEAR_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemClear"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["field"] == "app"
    assert data["errors"][0]["code"] == "INVALID"


def test_app_problem_clear_by_staff_with_aggregate_filter(
    staff_api_client, app, permission_manage_apps
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_apps)
    AppProblem.objects.create(
        app=app, type=AppProblemType.OWN, message="Problem 1", aggregate="group-a"
    )
    AppProblem.objects.create(
        app=app, type=AppProblemType.OWN, message="Problem 2", aggregate="group-b"
    )
    variables = {
        "app": graphene.Node.to_global_id("App", app.id),
        "aggregate": "group-a",
    }

    # when
    response = staff_api_client.post_graphql(APP_PROBLEM_CLEAR_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemClear"]
    assert not data["errors"]
    remaining = AppProblem.objects.filter(app=app)
    assert remaining.count() == 1
    assert remaining.first().aggregate == "group-b"


def test_app_problem_clear_by_staff_with_key_filter(
    staff_api_client, app, permission_manage_apps
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_apps)
    AppProblem.objects.create(
        app=app, type=AppProblemType.OWN, message="Keyed", key="my-key"
    )
    AppProblem.objects.create(
        app=app, type=AppProblemType.OWN, message="Other", key="other-key"
    )
    variables = {
        "app": graphene.Node.to_global_id("App", app.id),
        "key": "my-key",
    }

    # when
    response = staff_api_client.post_graphql(APP_PROBLEM_CLEAR_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemClear"]
    assert not data["errors"]
    remaining = AppProblem.objects.filter(app=app)
    assert remaining.count() == 1
    assert remaining.first().key == "other-key"


def test_app_problem_clear_by_staff_out_of_scope_app(
    staff_api_client, app, permission_manage_apps
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_apps)
    # Give the target app a permission the staff user doesn't have, making it
    # out of scope.
    from .....permission.models import Permission

    extra_perm = Permission.objects.get(codename="manage_orders")
    app.permissions.add(extra_perm)

    variables = {"app": graphene.Node.to_global_id("App", app.id)}

    # when
    response = staff_api_client.post_graphql(APP_PROBLEM_CLEAR_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemClear"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["field"] == "app"
    assert data["errors"][0]["code"] == "OUT_OF_SCOPE_APP"


def test_app_problem_clear_by_key(app_api_client, app):
    # given
    AppProblem.objects.create(
        app=app, type=AppProblemType.OWN, message="Keyed", key="my-key"
    )
    AppProblem.objects.create(
        app=app, type=AppProblemType.OWN, message="Other", key="other-key"
    )
    AppProblem.objects.create(app=app, type=AppProblemType.OWN, message="No key")
    variables = {"key": "my-key"}

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_CLEAR_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemClear"]
    assert not data["errors"]
    remaining = AppProblem.objects.filter(app=app)
    assert remaining.count() == 2
    assert not remaining.filter(key="my-key").exists()


def test_app_problem_clear_aggregate_and_key_fails(app_api_client, app):
    # given
    variables = {"aggregate": "group-a", "key": "my-key"}

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_CLEAR_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemClear"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["code"] == "INVALID"
    assert data["errors"][0]["field"] == "key"
