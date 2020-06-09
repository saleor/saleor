import graphene

from saleor.core import JobStatus
from saleor.csv import ExportEvents
from saleor.graphql.tests.utils import get_graphql_content

EXPORT_FILE_QUERY = """
    query($id: ID!){
        exportFile(id: $id){
            id
            status
            createdAt
            updatedAt
            url
            user{
                email
            }
            events{
                date
                type
                user{
                    email
                }
                message
            }
        }
    }
"""


def test_query_export_file(
    staff_api_client, export_file, permission_manage_products, export_event
):
    query = EXPORT_FILE_QUERY
    variables = {"id": graphene.Node.to_global_id("ExportFile", export_file.pk)}

    response = staff_api_client.post_graphql(
        query, variables=variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["exportFile"]

    assert data["status"] == JobStatus.PENDING.upper()
    assert data["createdAt"]
    assert data["updatedAt"]
    assert not data["url"]
    assert data["user"]["email"] == staff_api_client.user.email
    assert len(data["events"]) == 1
    event = data["events"][0]
    assert event["date"]
    assert event["message"] == export_event.parameters.get("message")
    assert event["type"] == ExportEvents.EXPORT_FAILED.upper()
    assert event["user"]["email"] == export_event.user.email


def test_query_export_file_as_app(
    app_api_client,
    export_file,
    permission_manage_products,
    permission_manage_users,
    export_event,
):
    query = EXPORT_FILE_QUERY
    variables = {"id": graphene.Node.to_global_id("ExportFile", export_file.pk)}

    response = app_api_client.post_graphql(
        query,
        variables=variables,
        permissions=[permission_manage_products, permission_manage_users],
    )
    content = get_graphql_content(response)
    data = content["data"]["exportFile"]

    assert data["status"] == JobStatus.PENDING.upper()
    assert data["createdAt"]
    assert data["updatedAt"]
    assert not data["url"]
    assert data["user"]["email"] == export_file.user.email
    assert len(data["events"]) == 1
    event = data["events"][0]
    assert event["date"]
    assert event["message"] == export_event.parameters.get("message")
    assert event["type"] == ExportEvents.EXPORT_FAILED.upper()
    assert event["user"]["email"] == export_event.user.email
