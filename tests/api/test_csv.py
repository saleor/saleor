import datetime
from unittest.mock import ANY, patch

import graphene
import pytest
from django.utils import timezone

from saleor.account.models import User
from saleor.csv import JobStatus
from saleor.csv.models import Job
from saleor.graphql.csv.enums import ExportScope
from tests.api.utils import get_graphql_content

EXPORT_PRODUCTS_MUTATION = """
    mutation ExportProducts($input: ExportProductsInput!){
        exportProducts(input: $input){
            job {
                id
                status
                createdAt
                completedAt
                url
                createdBy {
                    email
                }
            }
            csvErrors {
                field
                code
                message
            }
        }
    }
"""


@pytest.mark.parametrize(
    "input, called_data",
    [
        ({"scope": ExportScope.ALL.name}, {"all": ""}),
        (
            {"scope": ExportScope.FILTER.name, "filter": {"isPublished": True}},
            {"filter": {"is_published": True}},
        ),
    ],
)
@patch("saleor.graphql.csv.mutations.export_products.delay")
def test_export_products_mutation(
    export_products_mock,
    staff_api_client,
    product_list,
    permission_manage_products,
    input,
    called_data,
):
    query = EXPORT_PRODUCTS_MUTATION
    variables = {"input": input}

    response = staff_api_client.post_graphql(
        query, variables=variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["exportProducts"]
    job_data = data["job"]

    export_products_mock.assert_called_once_with(ANY, called_data)

    assert not data["csvErrors"]
    assert data["job"]["id"]
    assert job_data["createdAt"]
    assert job_data["createdBy"]["email"] == staff_api_client.user.email


@patch("saleor.graphql.csv.mutations.export_products.delay")
def test_export_products_mutation_ids_scope(
    export_products_mock, staff_api_client, product_list, permission_manage_products
):
    query = EXPORT_PRODUCTS_MUTATION

    products = product_list[:2]

    ids = []
    pks = set()
    for product in products:
        pks.add(str(product.pk))
        ids.append(graphene.Node.to_global_id("Product", product.pk))

    variables = {"input": {"scope": ExportScope.IDS.name, "ids": ids}}

    response = staff_api_client.post_graphql(
        query, variables=variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["exportProducts"]
    job_data = data["job"]

    export_products_mock.assert_called_once()
    (call_args, call_kwargs,) = export_products_mock.call_args

    assert set(call_args[1]["ids"]) == pks

    assert not data["csvErrors"]
    assert data["job"]["id"]
    assert job_data["createdAt"]
    assert job_data["createdBy"]["email"] == staff_api_client.user.email


@pytest.mark.parametrize(
    "input, error_field",
    [
        ({"scope": ExportScope.FILTER.name}, "filter"),
        ({"scope": ExportScope.IDS.name}, "ids"),
    ],
)
@patch("saleor.graphql.csv.mutations.export_products.delay")
def test_export_products_mutation_failed(
    export_products_mock,
    staff_api_client,
    product_list,
    permission_manage_products,
    input,
    error_field,
):
    query = EXPORT_PRODUCTS_MUTATION
    variables = {"input": input}

    response = staff_api_client.post_graphql(
        query, variables=variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["exportProducts"]
    errors = data["csvErrors"]

    export_products_mock.assert_not_called()

    assert data["csvErrors"]
    assert errors[0]["field"] == error_field


JOB_QUERY = """
    query($jobId: ID!){
        job(id: $jobId){
            id
            status
            completedAt
            createdAt
            url
            createdBy{
                email
            }
        }
    }
"""


FILTER_JOBS_QUERY = """
    query($filter: JobFilterInput!){
        jobs(first: 10, filter: $filter) {
            edges{
                node {
                    id
                    status
                    completedAt
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


SORT_JOBS_QUERY = """
    query($sortBy: JobSortingInput!) {
        jobs(first: 10, sortBy: $sortBy) {
            edges{
                node {
                    id
                    status
                    completedAt
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


def test_query_job(staff_api_client, job, permission_manage_products):
    query = JOB_QUERY
    variables = {"jobId": graphene.Node.to_global_id("Job", job.pk)}

    response = staff_api_client.post_graphql(
        query, variables=variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["job"]

    assert data["status"] == JobStatus.PENDING.upper()
    assert data["createdAt"]
    assert not data["completedAt"]
    assert not data["url"]
    assert data["createdBy"]["email"] == staff_api_client.user.email


@pytest.mark.parametrize(
    "status_filter, count",
    [
        ({"status": JobStatus.SUCCESS.upper()}, 2),
        ({"status": JobStatus.PENDING.upper()}, 2),
        ({"status": JobStatus.FAILED.upper()}, 1),
    ],
)
def test_filter_jobs_by_status(
    staff_api_client, job_list, permission_manage_products, status_filter, count
):
    query = FILTER_JOBS_QUERY
    variables = {"filter": status_filter}

    response = staff_api_client.post_graphql(
        query, variables=variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    nodes = content["data"]["jobs"]["edges"]

    assert len(nodes) == count


@pytest.mark.parametrize(
    "created_at_filter, count",
    [
        ({"createdAt": {"gte": "2019-04-10T00:00:00+00:00"}}, 3),
        ({"createdAt": {"lte": "2019-04-10T00:00:00+00:00"}}, 2),
    ],
)
def test_filter_jobs_by_created_at_date(
    staff_api_client, job_list, permission_manage_products, created_at_filter, count
):
    query = FILTER_JOBS_QUERY
    variables = {"filter": created_at_filter}

    response = staff_api_client.post_graphql(
        query, variables=variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    nodes = content["data"]["jobs"]["edges"]

    assert len(nodes) == count


@pytest.mark.parametrize(
    "ended_at_filter, count",
    [
        ({"completedAt": {"gte": "2019-04-18T00:00:00+00:00"}}, 3),
        ({"completedAt": {"lte": "2019-04-18T00:00:00+00:00"}}, 2),
    ],
)
def test_filter_jobs_by_ended_at_date(
    staff_api_client, job_list, permission_manage_products, ended_at_filter, count
):
    query = FILTER_JOBS_QUERY
    variables = {"filter": ended_at_filter}

    response = staff_api_client.post_graphql(
        query, variables=variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    nodes = content["data"]["jobs"]["edges"]

    assert len(nodes) == count


def test_filter_jobs_by_user(
    staff_api_client, job_list, permission_manage_products, staff_user
):
    second_staff_user = User.objects.create_user(
        email="staff_test2@example.com",
        password="password",
        is_staff=True,
        is_active=True,
    )

    job_list[1].created_by = second_staff_user
    job_list[1].save()

    query = FILTER_JOBS_QUERY
    variables = {"filter": {"createdBy": staff_user.email}}

    response = staff_api_client.post_graphql(
        query, variables=variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    nodes = content["data"]["jobs"]["edges"]

    assert len(nodes) == 4


def test_sort_jobs_query_by_user(
    staff_api_client, job, permission_manage_products, permission_manage_users
):
    second_staff_user = User.objects.create_user(
        email="staff_test2@example.com",
        password="password",
        is_staff=True,
        is_active=True,
    )

    Job.objects.create(created_by=second_staff_user)
    query = SORT_JOBS_QUERY
    variables = {"sortBy": {"field": "CREATED_BY", "direction": "DESC"}}

    response = staff_api_client.post_graphql(
        query,
        variables=variables,
        permissions=[permission_manage_products, permission_manage_users],
    )
    content = get_graphql_content(response)
    nodes = content["data"]["jobs"]["edges"]

    assert len(nodes) == 2
    assert nodes[0]["node"]["createdBy"]["email"] == second_staff_user.email


def test_sort_jobs_query_by_created_at_date(
    staff_api_client, job, permission_manage_products, staff_user
):
    second_job = Job.objects.create(created_by=staff_user)
    second_job.created_at = job.created_at - datetime.timedelta(minutes=10)
    second_job.save()

    query = SORT_JOBS_QUERY
    variables = {"sortBy": {"field": "CREATED_AT", "direction": "ASC"}}

    response = staff_api_client.post_graphql(
        query, variables=variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    nodes = content["data"]["jobs"]["edges"]

    assert len(nodes) == 2
    assert nodes[0]["node"]["id"] == graphene.Node.to_global_id("Job", second_job.pk)


def test_sort_jobs_query_by_ended_at_date(
    staff_api_client, job, permission_manage_products, staff_user
):
    job.completed_at = datetime.datetime(
        2010, 2, 19, tzinfo=timezone.get_current_timezone()
    )
    job.save()

    second_job = Job.objects.create(created_by=staff_user)
    second_job.completed_at = job.completed_at + datetime.timedelta(minutes=10)
    second_job.save()

    query = SORT_JOBS_QUERY
    variables = {"sortBy": {"field": "COMPLETED_AT", "direction": "ASC"}}

    response = staff_api_client.post_graphql(
        query, variables=variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    nodes = content["data"]["jobs"]["edges"]

    assert len(nodes) == 2
    assert nodes[0]["node"]["id"] == graphene.Node.to_global_id("Job", job.pk)


def test_sort_jobs_query_by_status(
    staff_api_client, job_list, permission_manage_products, staff_user
):
    query = SORT_JOBS_QUERY
    variables = {"sortBy": {"field": "STATUS", "direction": "ASC"}}

    response = staff_api_client.post_graphql(
        query, variables=variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    nodes = content["data"]["jobs"]["edges"]

    assert len(nodes) == 5
    status_result = [node["node"]["status"] for node in nodes]
    assert status_result == ["FAILED", "PENDING", "PENDING", "SUCCESS", "SUCCESS"]
