import base64

import graphene

from .....app.error_codes import AppProblemDismissErrorCode
from ....tests.utils import assert_no_permission, get_graphql_content

APP_PROBLEM_DISMISS_MUTATION = """
    mutation AppProblemDismiss($input: AppProblemDismissInput!) {
        appProblemDismiss(input: $input) {
            errors {
                field
                code
                message
            }
        }
    }
"""


def test_app_problem_dismiss_multiple_inputs_fails(
    app_api_client, app, app_problem_generator
):
    # given
    p1 = app_problem_generator(app)
    variables = {
        "input": {
            "byApp": {"ids": [graphene.Node.to_global_id("AppProblem", p1.id)]},
            "byStaffWithIds": {
                "ids": [graphene.Node.to_global_id("AppProblem", p1.id)]
            },
        }
    }

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_DISMISS_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemDismiss"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["field"] is None
    assert data["errors"][0]["code"] == "GRAPHQL_ERROR"
    assert (
        data["errors"][0]["message"]
        == "Argument 'byApp' cannot be combined with 'byStaffWithIds'"
    )


def test_app_problem_dismiss_no_input_fails(app_api_client, app):
    # given
    variables = {"input": {}}

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_DISMISS_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemDismiss"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["field"] is None
    assert data["errors"][0]["code"] == "GRAPHQL_ERROR"
    assert (
        data["errors"][0]["message"]
        == "At least one of arguments is required: 'byApp', 'byStaffWithIds', 'byStaffWithKeys'."
    )


def test_app_problem_dismiss_empty_by_app_fails(app_api_client, app):
    # given - byApp provided but without ids or keys
    variables = {"input": {"byApp": {}}}

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_DISMISS_MUTATION, variables)
    content = get_graphql_content(response)

    # then - empty byApp ({}) is falsy, so treated as not provided
    data = content["data"]["appProblemDismiss"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["field"] is None
    assert data["errors"][0]["code"] == "GRAPHQL_ERROR"
    assert (
        data["errors"][0]["message"]
        == "At least one of arguments is required: 'byApp', 'byStaffWithIds', 'byStaffWithKeys'."
    )


def test_app_problem_dismiss_without_permission(
    staff_api_client, app, app_problem_generator
):
    # given
    p1 = app_problem_generator(app)
    variables = {
        "input": {
            "byStaffWithIds": {"ids": [graphene.Node.to_global_id("AppProblem", p1.id)]}
        }
    }

    # when
    response = staff_api_client.post_graphql(APP_PROBLEM_DISMISS_MUTATION, variables)

    # then
    assert_no_permission(response)


def test_app_problem_dismiss_with_non_integer_id_fails(app_api_client, app):
    # given - ID with UUID instead of integer pk
    invalid_id = base64.b64encode(
        b"AppProblem:a7f47ac1-058c-4372-a567-0e02b2c3d479"
    ).decode("utf-8")
    variables = {"input": {"byApp": {"ids": [invalid_id]}}}

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_DISMISS_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemDismiss"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["field"] == "ids"
    assert data["errors"][0]["code"] == AppProblemDismissErrorCode.INVALID.name
    assert "Invalid ID" in data["errors"][0]["message"]
