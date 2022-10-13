import datetime

import graphene
import pytest
from django.utils import timezone

from .....account.models import User
from .....app.models import App
from .....core import JobStatus
from .....csv.models import ExportFile
from ....tests.utils import get_graphql_content

FILTER_EXPORT_FILES_QUERY = """
    query($filter: ExportFileFilterInput!){
        exportFiles(first: 10, filter: $filter) {
            edges{
                node {
                    id
                    status
                    createdAt
                    updatedAt
                    url
                    user{
                        email
                    }
                    app{
                        name
                    }
                }
            }
        }
    }
"""


SORT_EXPORT_FILES_QUERY = """
    query($sortBy: ExportFileSortingInput!) {
        exportFiles(first: 10, sortBy: $sortBy) {
            edges{
                node {
                    id
                    status
                    updatedAt
                    createdAt
                    url
                    user{
                        email
                    }
                    app{
                        name
                    }
                }
            }
        }
    }
"""


@pytest.mark.parametrize(
    "status_filter, count",
    [
        ({"status": JobStatus.SUCCESS.upper()}, 2),
        ({"status": JobStatus.PENDING.upper()}, 2),
        ({"status": JobStatus.FAILED.upper()}, 1),
    ],
)
def test_filter_export_files_by_status(
    staff_api_client,
    export_file_list,
    permission_manage_products,
    permission_manage_apps,
    status_filter,
    count,
):
    query = FILTER_EXPORT_FILES_QUERY
    variables = {"filter": status_filter}

    response = staff_api_client.post_graphql(
        query,
        variables=variables,
        permissions=[permission_manage_products, permission_manage_apps],
    )
    content = get_graphql_content(response)
    nodes = content["data"]["exportFiles"]["edges"]

    assert len(nodes) == count


@pytest.mark.parametrize(
    "created_at_filter, count",
    [
        ({"createdAt": {"gte": "2019-04-10T00:00:00+00:00"}}, 3),
        ({"createdAt": {"lte": "2019-04-10T00:00:00+00:00"}}, 2),
    ],
)
def test_filter_export_files_by_created_at_date(
    staff_api_client,
    export_file_list,
    permission_manage_products,
    permission_manage_apps,
    created_at_filter,
    count,
):
    query = FILTER_EXPORT_FILES_QUERY
    variables = {"filter": created_at_filter}

    response = staff_api_client.post_graphql(
        query,
        variables=variables,
        permissions=[permission_manage_products, permission_manage_apps],
    )
    content = get_graphql_content(response)
    nodes = content["data"]["exportFiles"]["edges"]

    assert len(nodes) == count


@pytest.mark.parametrize(
    "ended_at_filter, count",
    [
        ({"updatedAt": {"gte": "2019-04-18T00:00:00+00:00"}}, 3),
        ({"updatedAt": {"lte": "2019-04-18T00:00:00+00:00"}}, 2),
    ],
)
def test_filter_export_files_by_ended_at_date(
    staff_api_client,
    export_file_list,
    permission_manage_products,
    permission_manage_apps,
    ended_at_filter,
    count,
):
    query = FILTER_EXPORT_FILES_QUERY
    variables = {"filter": ended_at_filter}

    response = staff_api_client.post_graphql(
        query,
        variables=variables,
        permissions=[permission_manage_products, permission_manage_apps],
    )
    content = get_graphql_content(response)
    nodes = content["data"]["exportFiles"]["edges"]

    assert len(nodes) == count


def test_filter_export_files_by_user(
    staff_api_client,
    export_file_list,
    permission_manage_products,
    permission_manage_apps,
    staff_user,
):
    second_staff_user = User.objects.create_user(
        email="staff_test2@example.com",
        password="password",
        is_staff=True,
        is_active=True,
    )

    export_file_list[1].user = second_staff_user
    export_file_list[1].save()

    query = FILTER_EXPORT_FILES_QUERY
    variables = {"filter": {"user": staff_user.email}}

    response = staff_api_client.post_graphql(
        query,
        variables=variables,
        permissions=[permission_manage_products, permission_manage_apps],
    )
    content = get_graphql_content(response)
    nodes = content["data"]["exportFiles"]["edges"]

    assert len(nodes) == 4


def test_filter_export_files_by_app(
    staff_api_client,
    export_file_list,
    permission_manage_products,
    permission_manage_apps,
    permission_manage_staff,
    app,
):
    app2 = App.objects.create(name="Another app", is_active=True)
    app2.tokens.create(name="Default")

    export_file_list[0].user = None
    export_file_list[0].app = app

    export_file_list[1].user = None
    export_file_list[1].app = app

    export_file_list[2].user = None
    export_file_list[2].app = app2

    ExportFile.objects.bulk_update(export_file_list[:3], ["app", "user"])

    query = FILTER_EXPORT_FILES_QUERY
    variables = {"filter": {"app": app.name}}

    response = staff_api_client.post_graphql(
        query,
        variables=variables,
        permissions=[
            permission_manage_products,
            permission_manage_apps,
            permission_manage_staff,
        ],
    )
    content = get_graphql_content(response)
    nodes = content["data"]["exportFiles"]["edges"]

    assert len(nodes) == 2


def test_sort_export_files_query_by_created_at_date(
    staff_api_client,
    user_export_file,
    permission_manage_products,
    permission_manage_apps,
    staff_user,
):
    second_export_file = ExportFile.objects.create(user=staff_user)
    second_export_file.created_at = user_export_file.created_at - datetime.timedelta(
        minutes=10
    )
    second_export_file.save()

    query = SORT_EXPORT_FILES_QUERY
    variables = {"sortBy": {"field": "CREATED_AT", "direction": "ASC"}}

    response = staff_api_client.post_graphql(
        query,
        variables=variables,
        permissions=[permission_manage_products, permission_manage_apps],
    )
    content = get_graphql_content(response)
    nodes = content["data"]["exportFiles"]["edges"]

    assert len(nodes) == 2
    assert nodes[0]["node"]["id"] == graphene.Node.to_global_id(
        "ExportFile", second_export_file.pk
    )


@pytest.mark.parametrize("sort_by", ["UPDATED_AT", "LAST_MODIFIED_AT"])
def test_sort_export_files_query_by_updated_at_date(
    sort_by,
    staff_api_client,
    user_export_file,
    permission_manage_products,
    permission_manage_apps,
    staff_user,
):
    user_export_file.updated_at = datetime.datetime(
        2010, 2, 19, tzinfo=timezone.get_current_timezone()
    )
    user_export_file.save()

    second_export_file = ExportFile.objects.create(user=staff_user)
    second_export_file.updated_at = user_export_file.updated_at + datetime.timedelta(
        minutes=10
    )
    second_export_file.save()

    query = SORT_EXPORT_FILES_QUERY
    variables = {"sortBy": {"field": sort_by, "direction": "ASC"}}

    response = staff_api_client.post_graphql(
        query,
        variables=variables,
        permissions=[permission_manage_products, permission_manage_apps],
    )
    content = get_graphql_content(response)
    nodes = content["data"]["exportFiles"]["edges"]

    assert len(nodes) == 2
    assert nodes[0]["node"]["id"] == graphene.Node.to_global_id(
        "ExportFile", user_export_file.pk
    )


def test_sort_export_files_query_by_status(
    staff_api_client,
    export_file_list,
    permission_manage_products,
    permission_manage_apps,
    staff_user,
):
    query = SORT_EXPORT_FILES_QUERY
    variables = {"sortBy": {"field": "STATUS", "direction": "ASC"}}

    response = staff_api_client.post_graphql(
        query,
        variables=variables,
        permissions=[permission_manage_products, permission_manage_apps],
    )
    content = get_graphql_content(response)
    nodes = content["data"]["exportFiles"]["edges"]

    assert len(nodes) == 5
    status_result = [node["node"]["status"] for node in nodes]
    assert status_result == ["FAILED", "PENDING", "PENDING", "SUCCESS", "SUCCESS"]
