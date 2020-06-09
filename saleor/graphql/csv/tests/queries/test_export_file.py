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
            app{
                name
            }
            events{
                date
                type
                user{
                    email
                }
                message
                app{
                    name
                }
            }
        }
    }
"""


def test_query_export_file(
    staff_api_client,
    export_file,
    permission_manage_products,
    permission_manage_apps,
    export_event,
):
    query = EXPORT_FILE_QUERY
    variables = {"id": graphene.Node.to_global_id("ExportFile", export_file.pk)}

    response = staff_api_client.post_graphql(
        query,
        variables=variables,
        permissions=[permission_manage_products, permission_manage_apps],
    )
    content = get_graphql_content(response)
    data = content["data"]["exportFile"]

    assert data["status"] == JobStatus.PENDING.upper()
    assert data["createdAt"]
    assert data["updatedAt"]
    assert data["app"] is None
    assert not data["url"]
    assert data["user"]["email"] == staff_api_client.user.email
    assert len(data["events"]) == 1
    event = data["events"][0]
    assert event["date"]
    assert event["message"] == export_event.parameters.get("message")
    assert event["type"] == ExportEvents.EXPORT_FAILED.upper()
    assert event["user"]["email"] == export_event.user.email
    assert event["app"] is None


def test_query_export_file_export_file_with_app(
    app,
    staff_api_client,
    export_file,
    permission_manage_products,
    permission_manage_apps,
    permission_manage_users,
    export_event,
):
    export_file.user = None
    export_file.app = app
    export_file.save(update_fields=["user", "app"])

    export_event.user = None
    export_event.app = app
    export_event.save(update_fields=["user", "app"])

    query = EXPORT_FILE_QUERY
    variables = {"id": graphene.Node.to_global_id("ExportFile", export_file.pk)}

    response = staff_api_client.post_graphql(
        query,
        variables=variables,
        permissions=[
            permission_manage_products,
            permission_manage_users,
            permission_manage_apps,
        ],
    )
    content = get_graphql_content(response)
    data = content["data"]["exportFile"]

    assert data["status"] == JobStatus.PENDING.upper()
    assert data["createdAt"]
    assert data["updatedAt"]
    assert data["app"]["name"] == app.name
    assert not data["url"]
    assert data["user"] is None
    assert len(data["events"]) == 1
    event = data["events"][0]
    assert event["date"]
    assert event["message"] == export_event.parameters.get("message")
    assert event["type"] == ExportEvents.EXPORT_FAILED.upper()
    assert event["user"] is None
    assert event["app"]["name"] == app.name


def test_query_export_file_as_app(
    app_api_client,
    export_file,
    permission_manage_products,
    permission_manage_users,
    permission_manage_apps,
    export_event,
):
    query = EXPORT_FILE_QUERY
    variables = {"id": graphene.Node.to_global_id("ExportFile", export_file.pk)}

    response = app_api_client.post_graphql(
        query,
        variables=variables,
        permissions=[
            permission_manage_products,
            permission_manage_users,
            permission_manage_apps,
        ],
    )
    content = get_graphql_content(response)
    data = content["data"]["exportFile"]

    assert data["status"] == JobStatus.PENDING.upper()
    assert data["createdAt"]
    assert data["updatedAt"]
    assert data["app"] is None
    assert not data["url"]
    assert data["user"]["email"] == export_file.user.email
    assert len(data["events"]) == 1
    event = data["events"][0]
    assert event["date"]
    assert event["message"] == export_event.parameters.get("message")
    assert event["type"] == ExportEvents.EXPORT_FAILED.upper()
    assert event["user"]["email"] == export_event.user.email
    assert event["app"] is None
