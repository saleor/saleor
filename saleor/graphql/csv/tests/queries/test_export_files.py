import datetime

import graphene
import pytest
from django.utils import timezone

from saleor.account.models import User
from saleor.core import JobStatus
from saleor.csv.models import ExportFile
from saleor.graphql.tests.utils import get_graphql_content

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
                    createdBy{
                        email
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
                    createdBy{
                        email
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
    staff_api_client, export_file_list, permission_manage_products, status_filter, count
):
    query = FILTER_EXPORT_FILES_QUERY
    variables = {"filter": status_filter}

    response = staff_api_client.post_graphql(
        query, variables=variables, permissions=[permission_manage_products]
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
    created_at_filter,
    count,
):
    query = FILTER_EXPORT_FILES_QUERY
    variables = {"filter": created_at_filter}

    response = staff_api_client.post_graphql(
        query, variables=variables, permissions=[permission_manage_products]
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
    ended_at_filter,
    count,
):
    query = FILTER_EXPORT_FILES_QUERY
    variables = {"filter": ended_at_filter}

    response = staff_api_client.post_graphql(
        query, variables=variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    nodes = content["data"]["exportFiles"]["edges"]

    assert len(nodes) == count


def test_filter_export_files_by_user(
    staff_api_client, export_file_list, permission_manage_products, staff_user
):
    second_staff_user = User.objects.create_user(
        email="staff_test2@example.com",
        password="password",
        is_staff=True,
        is_active=True,
    )

    export_file_list[1].created_by = second_staff_user
    export_file_list[1].save()

    query = FILTER_EXPORT_FILES_QUERY
    variables = {"filter": {"createdBy": staff_user.email}}

    response = staff_api_client.post_graphql(
        query, variables=variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    nodes = content["data"]["exportFiles"]["edges"]

    assert len(nodes) == 4


def test_sort_export_files_query_by_user(
    staff_api_client, export_file, permission_manage_products, permission_manage_users
):
    second_staff_user = User.objects.create_user(
        email="staff_test2@example.com",
        password="password",
        is_staff=True,
        is_active=True,
    )

    ExportFile.objects.create(created_by=second_staff_user)
    query = SORT_EXPORT_FILES_QUERY
    variables = {"sortBy": {"field": "CREATED_BY", "direction": "DESC"}}

    response = staff_api_client.post_graphql(
        query,
        variables=variables,
        permissions=[permission_manage_products, permission_manage_users],
    )
    content = get_graphql_content(response)
    nodes = content["data"]["exportFiles"]["edges"]

    assert len(nodes) == 2
    assert nodes[0]["node"]["createdBy"]["email"] == second_staff_user.email


def test_sort_export_files_query_by_created_at_date(
    staff_api_client, export_file, permission_manage_products, staff_user
):
    second_export_file = ExportFile.objects.create(created_by=staff_user)
    second_export_file.created_at = export_file.created_at - datetime.timedelta(
        minutes=10
    )
    second_export_file.save()

    query = SORT_EXPORT_FILES_QUERY
    variables = {"sortBy": {"field": "CREATED_AT", "direction": "ASC"}}

    response = staff_api_client.post_graphql(
        query, variables=variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    nodes = content["data"]["exportFiles"]["edges"]

    assert len(nodes) == 2
    assert nodes[0]["node"]["id"] == graphene.Node.to_global_id(
        "ExportFile", second_export_file.pk
    )


def test_sort_export_files_query_by_updated_at_date(
    staff_api_client, export_file, permission_manage_products, staff_user
):
    export_file.updated_at = datetime.datetime(
        2010, 2, 19, tzinfo=timezone.get_current_timezone()
    )
    export_file.save()

    second_export_file = ExportFile.objects.create(created_by=staff_user)
    second_export_file.updated_at = export_file.updated_at + datetime.timedelta(
        minutes=10
    )
    second_export_file.save()

    query = SORT_EXPORT_FILES_QUERY
    variables = {"sortBy": {"field": "UPDATED_AT", "direction": "ASC"}}

    response = staff_api_client.post_graphql(
        query, variables=variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    nodes = content["data"]["exportFiles"]["edges"]

    assert len(nodes) == 2
    assert nodes[0]["node"]["id"] == graphene.Node.to_global_id(
        "ExportFile", export_file.pk
    )


def test_sort_export_files_query_by_status(
    staff_api_client, export_file_list, permission_manage_products, staff_user
):
    query = SORT_EXPORT_FILES_QUERY
    variables = {"sortBy": {"field": "STATUS", "direction": "ASC"}}

    response = staff_api_client.post_graphql(
        query, variables=variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    nodes = content["data"]["exportFiles"]["edges"]

    assert len(nodes) == 5
    status_result = [node["node"]["status"] for node in nodes]
    assert status_result == ["FAILED", "PENDING", "PENDING", "SUCCESS", "SUCCESS"]
