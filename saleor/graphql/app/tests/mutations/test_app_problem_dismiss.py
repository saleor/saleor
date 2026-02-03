import graphene
from django.utils import timezone

from .....app.models import AppProblem
from ....tests.utils import assert_no_permission, get_graphql_content

APP_PROBLEM_DISMISS_MUTATION = """
    mutation AppProblemDismiss($ids: [ID!], $keys: [String!], $app: ID) {
        appProblemDismiss(ids: $ids, keys: $keys, app: $app) {
            app {
                id
                problems {
                    id
                    message
                    key
                    dismissed
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


def _create_problem(app, key="test-key", message="Test problem", dismissed=False):
    return AppProblem.objects.create(
        app=app,
        message=message,
        key=key,
        updated_at=timezone.now(),
        dismissed=dismissed,
    )


def test_app_problem_dismiss_by_ids_as_app(app_api_client, app):
    # given
    p1 = _create_problem(app, key="k1", message="Problem 1")
    p2 = _create_problem(app, key="k2", message="Problem 2")
    variables = {
        "ids": [
            graphene.Node.to_global_id("AppProblem", p1.id),
        ]
    }

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_DISMISS_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemDismiss"]
    assert not data["errors"]
    p1.refresh_from_db()
    p2.refresh_from_db()
    assert p1.dismissed is True
    assert p1.dismissed_by_app == app
    assert p2.dismissed is False


def test_app_problem_dismiss_by_keys_as_app(app_api_client, app):
    # given
    p1 = _create_problem(app, key="same-key", message="Problem 1")
    p2 = _create_problem(app, key="same-key", message="Problem 2")
    p3 = _create_problem(app, key="other-key", message="Problem 3")
    variables = {"keys": ["same-key"]}

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_DISMISS_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemDismiss"]
    assert not data["errors"]
    p1.refresh_from_db()
    p2.refresh_from_db()
    p3.refresh_from_db()
    assert p1.dismissed is True
    assert p2.dismissed is True
    assert p3.dismissed is False


def test_app_problem_dismiss_by_ids_as_staff(
    staff_api_client, app, permission_manage_apps
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_apps)
    p1 = _create_problem(app, key="k1")
    variables = {
        "ids": [graphene.Node.to_global_id("AppProblem", p1.id)],
    }

    # when
    response = staff_api_client.post_graphql(APP_PROBLEM_DISMISS_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemDismiss"]
    assert not data["errors"]
    p1.refresh_from_db()
    assert p1.dismissed is True
    assert p1.dismissed_by_user == staff_api_client.user


def test_app_problem_dismiss_by_keys_as_staff_requires_app_arg(
    staff_api_client, app, permission_manage_apps
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_apps)
    _create_problem(app, key="k1")
    variables = {"keys": ["k1"]}

    # when
    response = staff_api_client.post_graphql(APP_PROBLEM_DISMISS_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemDismiss"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["field"] == "app"
    assert data["errors"][0]["code"] == "REQUIRED"


def test_app_problem_dismiss_by_keys_as_staff_with_app_arg(
    staff_api_client, app, permission_manage_apps
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_apps)
    p1 = _create_problem(app, key="k1")
    variables = {
        "keys": ["k1"],
        "app": graphene.Node.to_global_id("App", app.id),
    }

    # when
    response = staff_api_client.post_graphql(APP_PROBLEM_DISMISS_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemDismiss"]
    assert not data["errors"]
    p1.refresh_from_db()
    assert p1.dismissed is True
    assert p1.dismissed_by_user == staff_api_client.user


def test_app_problem_dismiss_both_ids_and_keys_fails(app_api_client, app):
    # given
    p1 = _create_problem(app)
    variables = {
        "ids": [graphene.Node.to_global_id("AppProblem", p1.id)],
        "keys": ["test-key"],
    }

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_DISMISS_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemDismiss"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["code"] == "INVALID"


def test_app_problem_dismiss_neither_ids_nor_keys_fails(app_api_client, app):
    # when
    response = app_api_client.post_graphql(APP_PROBLEM_DISMISS_MUTATION)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemDismiss"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["code"] == "REQUIRED"


def test_app_problem_dismiss_app_caller_cannot_specify_app_arg(app_api_client, app):
    # given
    variables = {"app": graphene.Node.to_global_id("App", app.id), "keys": ["k1"]}

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_DISMISS_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemDismiss"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["field"] == "app"
    assert data["errors"][0]["code"] == "INVALID"


def test_app_problem_dismiss_without_permission(staff_api_client, app):
    # given
    p1 = _create_problem(app)
    variables = {"ids": [graphene.Node.to_global_id("AppProblem", p1.id)]}

    # when
    response = staff_api_client.post_graphql(APP_PROBLEM_DISMISS_MUTATION, variables)

    # then
    assert_no_permission(response)


def test_app_problem_dismiss_out_of_scope_app(
    staff_api_client, app, permission_manage_apps
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_apps)
    from .....permission.models import Permission

    extra_perm = Permission.objects.get(codename="manage_orders")
    app.permissions.add(extra_perm)

    variables = {
        "keys": ["k1"],
        "app": graphene.Node.to_global_id("App", app.id),
    }

    # when
    response = staff_api_client.post_graphql(APP_PROBLEM_DISMISS_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemDismiss"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["field"] == "app"
    assert data["errors"][0]["code"] == "OUT_OF_SCOPE_APP"


def test_app_problem_dismiss_idempotent(app_api_client, app):
    # given
    p1 = _create_problem(app, key="k1", dismissed=True)
    variables = {"ids": [graphene.Node.to_global_id("AppProblem", p1.id)]}

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_DISMISS_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemDismiss"]
    assert not data["errors"]
    p1.refresh_from_db()
    assert p1.dismissed is True
