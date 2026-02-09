import graphene

from .....app.models import AppProblem
from ....tests.utils import get_graphql_content, get_graphql_content_from_response

QUERY_APP_PROBLEMS = """
    query ($id: ID) {
        app(id: $id) {
            id
            problems {
                id
                message
                key
                createdAt
                updatedAt
                count
                isCritical
                dismissed
            }
        }
    }
"""

QUERY_APP_PROBLEMS_WITH_LIMIT = """
    query ($id: ID, $limit: PositiveInt) {
        app(id: $id) {
            id
            problems(limit: $limit) {
                id
                message
            }
        }
    }
"""


def test_app_problems_empty(app_api_client, app):
    # given
    variables = {"id": graphene.Node.to_global_id("App", app.id)}

    # when
    response = app_api_client.post_graphql(QUERY_APP_PROBLEMS, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["app"]
    assert data["problems"] == []


def test_app_problems_returns_problems(app_api_client, app):
    # given
    p1 = AppProblem.objects.create(app=app, message="Issue 1", key="k1")
    p2 = AppProblem.objects.create(app=app, message="Issue 2", key="k2")
    variables = {"id": graphene.Node.to_global_id("App", app.id)}

    # when
    response = app_api_client.post_graphql(QUERY_APP_PROBLEMS, variables)
    content = get_graphql_content(response)

    # then
    problems = content["data"]["app"]["problems"]
    assert len(problems) == 2
    # Ordered by created_at desc, so p2 comes first
    assert problems[0]["id"] == graphene.Node.to_global_id("AppProblem", p2.id)
    assert problems[0]["message"] == "Issue 2"
    assert problems[0]["key"] == "k2"
    assert problems[0]["count"] == 1
    assert problems[0]["isCritical"] is False
    assert problems[0]["dismissed"] is False
    assert problems[1]["id"] == graphene.Node.to_global_id("AppProblem", p1.id)
    assert problems[1]["message"] == "Issue 1"
    assert problems[1]["key"] == "k1"
    assert problems[1]["count"] == 1
    assert problems[1]["isCritical"] is False
    assert problems[1]["dismissed"] is False


def test_app_problems_ordered_by_created_at_desc(app_api_client, app):
    # given
    p1 = AppProblem.objects.create(app=app, message="First", key="k1")
    p2 = AppProblem.objects.create(app=app, message="Second", key="k2")
    variables = {"id": graphene.Node.to_global_id("App", app.id)}

    # when
    response = app_api_client.post_graphql(QUERY_APP_PROBLEMS, variables)
    content = get_graphql_content(response)

    # then
    problems = content["data"]["app"]["problems"]
    assert len(problems) == 2
    assert problems[0]["id"] == graphene.Node.to_global_id("AppProblem", p2.id)
    assert problems[0]["message"] == "Second"
    assert problems[0]["key"] == "k2"
    assert problems[1]["id"] == graphene.Node.to_global_id("AppProblem", p1.id)
    assert problems[1]["message"] == "First"
    assert problems[1]["key"] == "k1"


def test_app_problems_count_and_critical(app_api_client, app):
    # given
    AppProblem.objects.create(
        app=app, message="Normal", key="k1", count=3, is_critical=False
    )
    AppProblem.objects.create(
        app=app,
        message="Critical",
        key="k2",
        count=10,
        is_critical=True,
    )
    variables = {"id": graphene.Node.to_global_id("App", app.id)}

    # when
    response = app_api_client.post_graphql(QUERY_APP_PROBLEMS, variables)
    content = get_graphql_content(response)

    # then
    problems = content["data"]["app"]["problems"]
    by_msg = {p["message"]: p for p in problems}
    assert by_msg["Normal"]["count"] == 3
    assert by_msg["Normal"]["isCritical"] is False
    assert by_msg["Critical"]["count"] == 10
    assert by_msg["Critical"]["isCritical"] is True


def test_app_problems_dismissed_field(app_api_client, app):
    # given
    AppProblem.objects.create(app=app, message="Active", key="k1", dismissed=False)
    AppProblem.objects.create(app=app, message="Dismissed", key="k2", dismissed=True)
    variables = {"id": graphene.Node.to_global_id("App", app.id)}

    # when
    response = app_api_client.post_graphql(QUERY_APP_PROBLEMS, variables)
    content = get_graphql_content(response)

    # then
    problems = content["data"]["app"]["problems"]
    by_msg = {p["message"]: p for p in problems}
    assert by_msg["Active"]["dismissed"] is False
    assert by_msg["Dismissed"]["dismissed"] is True


QUERY_APP_PROBLEMS_WITH_DISMISSED_BY = """
    query ($id: ID) {
        app(id: $id) {
            id
            problems {
                id
                dismissed
                dismissedBy {
                    ... on App {
                        id
                        name
                    }
                    ... on User {
                        id
                        email
                    }
                }
            }
        }
    }
"""


def test_app_problems_dismissed_by_app(app_api_client, app):
    # given
    AppProblem.objects.create(
        app=app,
        message="Dismissed by app",
        key="k1",
        dismissed=True,
        # No dismissed_by_user_email means dismissed by app
    )
    variables = {"id": graphene.Node.to_global_id("App", app.id)}

    # when
    response = app_api_client.post_graphql(
        QUERY_APP_PROBLEMS_WITH_DISMISSED_BY, variables
    )
    content = get_graphql_content(response)

    # then
    problems = content["data"]["app"]["problems"]
    assert len(problems) == 1
    assert problems[0]["dismissed"] is True
    assert problems[0]["dismissedBy"]["name"] == app.name


def test_app_problems_dismissed_by_user(
    staff_api_client, app, permission_manage_apps, permission_manage_staff
):
    # given
    staff_api_client.user.user_permissions.add(
        permission_manage_apps, permission_manage_staff
    )
    staff_user = staff_api_client.user
    AppProblem.objects.create(
        app=app,
        message="Dismissed by user",
        key="k1",
        dismissed=True,
        dismissed_by_user_email=staff_user.email,
        dismissed_by_user=staff_user,
    )
    variables = {"id": graphene.Node.to_global_id("App", app.id)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_APP_PROBLEMS_WITH_DISMISSED_BY, variables
    )
    content = get_graphql_content(response)

    # then
    problems = content["data"]["app"]["problems"]
    assert len(problems) == 1
    assert problems[0]["dismissed"] is True
    assert problems[0]["dismissedBy"]["email"] == staff_user.email


def test_app_problems_dismissed_by_null_when_not_dismissed(app_api_client, app):
    # given
    AppProblem.objects.create(
        app=app,
        message="Not dismissed",
        key="k1",
        dismissed=False,
    )
    variables = {"id": graphene.Node.to_global_id("App", app.id)}

    # when
    response = app_api_client.post_graphql(
        QUERY_APP_PROBLEMS_WITH_DISMISSED_BY, variables
    )
    content = get_graphql_content(response)

    # then
    problems = content["data"]["app"]["problems"]
    assert len(problems) == 1
    assert problems[0]["dismissedBy"] is None


QUERY_APP_PROBLEMS_WITH_DISMISSED_BY_AND_EMAIL = """
    query ($id: ID) {
        app(id: $id) {
            id
            problems {
                id
                dismissed
                dismissedBy {
                    ... on App {
                        id
                        name
                    }
                    ... on User {
                        id
                        email
                    }
                }
                dismissedByUserEmail
            }
        }
    }
"""


def test_app_problems_dismissed_by_user_returns_null_when_user_deleted(
    staff_api_client, app, permission_manage_apps, permission_manage_staff
):
    # given - a problem was dismissed by a user who was later deleted
    staff_api_client.user.user_permissions.add(
        permission_manage_apps, permission_manage_staff
    )
    staff_user = staff_api_client.user
    problem = AppProblem.objects.create(
        app=app,
        message="Dismissed by deleted user",
        key="k1",
        dismissed=True,
        dismissed_by_user_email=staff_user.email,
        dismissed_by_user=staff_user,
    )

    # when - user is deleted (simulating SET_NULL behavior)
    problem.dismissed_by_user = None
    problem.save(update_fields=["dismissed_by_user"])

    variables = {"id": graphene.Node.to_global_id("App", app.id)}
    response = staff_api_client.post_graphql(
        QUERY_APP_PROBLEMS_WITH_DISMISSED_BY_AND_EMAIL, variables
    )
    content = get_graphql_content(response)

    # then - dismissedBy should be null, NOT the app (email is preserved)
    problems = content["data"]["app"]["problems"]
    assert len(problems) == 1
    assert problems[0]["dismissed"] is True
    assert problems[0]["dismissedBy"] is None
    assert problems[0]["dismissedByUserEmail"] == staff_user.email


def test_app_problems_cascade_delete(app, db):
    # given
    AppProblem.objects.create(app=app, message="To be deleted", key="k1")
    assert AppProblem.objects.count() == 1

    # when
    app.delete()

    # then
    assert AppProblem.objects.count() == 0


# Permission tests for dismissedByUserEmail field

QUERY_APP_PROBLEMS_WITH_EMAIL_ONLY = """
    query ($id: ID) {
        app(id: $id) {
            id
            problems {
                id
                dismissed
                dismissedByUserEmail
            }
        }
    }
"""


def test_app_cannot_see_dismissed_by_user_email(
    app_api_client, app, staff_user, permission_manage_apps, permission_manage_staff
):
    # given - apps cannot have MANAGE_STAFF permission in this codebase
    # even if we add the permission, it's explicitly blocked for apps
    app_api_client.app.permissions.add(permission_manage_apps, permission_manage_staff)
    AppProblem.objects.create(
        app=app,
        message="Problem",
        key="k1",
        dismissed=True,
        dismissed_by_user_email=staff_user.email,
        dismissed_by_user=staff_user,
    )
    variables = {"id": graphene.Node.to_global_id("App", app.id)}

    # when
    response = app_api_client.post_graphql(
        QUERY_APP_PROBLEMS_WITH_EMAIL_ONLY, variables
    )
    content = get_graphql_content_from_response(response)

    # then - apps cannot have MANAGE_STAFF, so they get permission denied
    assert "errors" in content
    assert content["errors"][0]["extensions"]["exception"]["code"] == "PermissionDenied"


def test_authenticated_user_can_see_dismissed_by_user_email(
    staff_api_client, app, permission_manage_apps
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_apps)
    staff_user = staff_api_client.user
    AppProblem.objects.create(
        app=app,
        message="Problem",
        key="k1",
        dismissed=True,
        dismissed_by_user_email=staff_user.email,
        dismissed_by_user=staff_user,
    )
    variables = {"id": graphene.Node.to_global_id("App", app.id)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_APP_PROBLEMS_WITH_EMAIL_ONLY, variables
    )
    content = get_graphql_content(response)

    # then
    problems = content["data"]["app"]["problems"]
    assert len(problems) == 1
    assert problems[0]["dismissedByUserEmail"] == staff_user.email


def test_app_without_manage_staff_cannot_see_dismissed_by_user_email(
    app_api_client, app, staff_user, permission_manage_apps
):
    # given - app has MANAGE_APPS but not MANAGE_STAFF
    app_api_client.app.permissions.add(permission_manage_apps)
    AppProblem.objects.create(
        app=app,
        message="Problem",
        key="k1",
        dismissed=True,
        dismissed_by_user_email=staff_user.email,
        dismissed_by_user=staff_user,
    )
    variables = {"id": graphene.Node.to_global_id("App", app.id)}

    # when
    response = app_api_client.post_graphql(
        QUERY_APP_PROBLEMS_WITH_EMAIL_ONLY, variables
    )
    content = get_graphql_content_from_response(response)

    # then
    assert "errors" in content
    assert content["errors"][0]["extensions"]["exception"]["code"] == "PermissionDenied"


# Permission tests for dismissedBy field - when dismissed by App


def test_app_can_see_dismissed_by_when_dismissed_by_app(app_api_client, app):
    # given
    AppProblem.objects.create(
        app=app,
        message="Dismissed by app",
        key="k1",
        dismissed=True,
        # No dismissed_by_user_email means dismissed by app
    )
    variables = {"id": graphene.Node.to_global_id("App", app.id)}

    # when
    response = app_api_client.post_graphql(
        QUERY_APP_PROBLEMS_WITH_DISMISSED_BY, variables
    )
    content = get_graphql_content(response)

    # then
    problems = content["data"]["app"]["problems"]
    assert len(problems) == 1
    assert problems[0]["dismissedBy"]["name"] == app.name


def test_authenticated_user_can_see_dismissed_by_when_dismissed_by_app(
    staff_api_client, app, permission_manage_apps
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_apps)
    AppProblem.objects.create(
        app=app,
        message="Dismissed by app",
        key="k1",
        dismissed=True,
        # No dismissed_by_user_email means dismissed by app
    )
    variables = {"id": graphene.Node.to_global_id("App", app.id)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_APP_PROBLEMS_WITH_DISMISSED_BY, variables
    )
    content = get_graphql_content(response)

    # then
    problems = content["data"]["app"]["problems"]
    assert len(problems) == 1
    assert problems[0]["dismissedBy"]["name"] == app.name


# Permission tests for dismissedBy field - when dismissed by User


def test_user_with_manage_staff_can_see_dismissed_by_when_dismissed_by_user(
    staff_api_client, app, permission_manage_apps, permission_manage_staff
):
    # given
    staff_api_client.user.user_permissions.add(
        permission_manage_apps, permission_manage_staff
    )
    staff_user = staff_api_client.user
    AppProblem.objects.create(
        app=app,
        message="Dismissed by user",
        key="k1",
        dismissed=True,
        dismissed_by_user_email=staff_user.email,
        dismissed_by_user=staff_user,
    )
    variables = {"id": graphene.Node.to_global_id("App", app.id)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_APP_PROBLEMS_WITH_DISMISSED_BY, variables
    )
    content = get_graphql_content(response)

    # then
    problems = content["data"]["app"]["problems"]
    assert len(problems) == 1
    assert problems[0]["dismissedBy"]["email"] == staff_user.email


def test_user_without_manage_staff_cannot_see_dismissed_by_when_dismissed_by_user(
    staff_api_client, app, staff_user, permission_manage_apps
):
    # given - user has MANAGE_APPS but not MANAGE_STAFF
    staff_api_client.user.user_permissions.add(permission_manage_apps)
    AppProblem.objects.create(
        app=app,
        message="Dismissed by user",
        key="k1",
        dismissed=True,
        dismissed_by_user_email=staff_user.email,
        dismissed_by_user=staff_user,
    )
    variables = {"id": graphene.Node.to_global_id("App", app.id)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_APP_PROBLEMS_WITH_DISMISSED_BY, variables
    )
    content = get_graphql_content_from_response(response)

    # then
    assert "errors" in content
    assert content["errors"][0]["extensions"]["exception"]["code"] == "PermissionDenied"


def test_app_cannot_see_dismissed_by_when_dismissed_by_user(
    app_api_client, app, staff_user, permission_manage_apps, permission_manage_staff
):
    # given - apps cannot have MANAGE_STAFF permission in this codebase
    # even if we add the permission, it's explicitly blocked for apps
    app_api_client.app.permissions.add(permission_manage_apps, permission_manage_staff)
    AppProblem.objects.create(
        app=app,
        message="Dismissed by user",
        key="k1",
        dismissed=True,
        dismissed_by_user_email=staff_user.email,
        dismissed_by_user=staff_user,
    )
    variables = {"id": graphene.Node.to_global_id("App", app.id)}

    # when
    response = app_api_client.post_graphql(
        QUERY_APP_PROBLEMS_WITH_DISMISSED_BY, variables
    )
    content = get_graphql_content_from_response(response)

    # then - apps cannot have MANAGE_STAFF, so they get permission denied
    assert "errors" in content
    assert content["errors"][0]["extensions"]["exception"]["code"] == "PermissionDenied"


def test_app_without_manage_staff_cannot_see_dismissed_by_when_dismissed_by_user(
    app_api_client, app, staff_user, permission_manage_apps
):
    # given - app has MANAGE_APPS but not MANAGE_STAFF
    app_api_client.app.permissions.add(permission_manage_apps)
    AppProblem.objects.create(
        app=app,
        message="Dismissed by user",
        key="k1",
        dismissed=True,
        dismissed_by_user_email=staff_user.email,
        dismissed_by_user=staff_user,
    )
    variables = {"id": graphene.Node.to_global_id("App", app.id)}

    # when
    response = app_api_client.post_graphql(
        QUERY_APP_PROBLEMS_WITH_DISMISSED_BY, variables
    )
    content = get_graphql_content_from_response(response)

    # then
    assert "errors" in content
    assert content["errors"][0]["extensions"]["exception"]["code"] == "PermissionDenied"


def test_app_problems_limit_negative(app_api_client, app):
    # given
    AppProblem.objects.create(app=app, message="Issue 1", key="k1")
    variables = {
        "id": graphene.Node.to_global_id("App", app.id),
        "limit": -1,
    }

    # when
    response = app_api_client.post_graphql(QUERY_APP_PROBLEMS_WITH_LIMIT, variables)
    content = get_graphql_content_from_response(response)

    # then
    assert len(content["errors"]) == 1
    assert 'Expected type "PositiveInt", found -1.' in content["errors"][0]["message"]


def test_app_problems_limit_zero(app_api_client, app):
    # given
    AppProblem.objects.create(app=app, message="Issue 1", key="k1")
    variables = {
        "id": graphene.Node.to_global_id("App", app.id),
        "limit": 0,
    }

    # when
    response = app_api_client.post_graphql(QUERY_APP_PROBLEMS_WITH_LIMIT, variables)
    content = get_graphql_content_from_response(response)

    # then
    assert len(content["errors"]) == 1
    assert 'Expected type "PositiveInt", found 0.' in content["errors"][0]["message"]


def test_app_problems_limit_one(app_api_client, app):
    # given
    AppProblem.objects.create(app=app, message="Issue 1", key="k1")
    p2 = AppProblem.objects.create(app=app, message="Issue 2", key="k2")
    variables = {
        "id": graphene.Node.to_global_id("App", app.id),
        "limit": 1,
    }

    # when
    response = app_api_client.post_graphql(QUERY_APP_PROBLEMS_WITH_LIMIT, variables)
    content = get_graphql_content(response)

    # then
    problems = content["data"]["app"]["problems"]
    assert len(problems) == 1
    assert problems[0]["id"] == graphene.Node.to_global_id("AppProblem", p2.id)
    assert problems[0]["message"] == "Issue 2"
