import graphene
from .....payment.error_codes import TransactionCreateErrorCode
from ....tests.utils import get_graphql_content

MUTATION_TRANSACTION_CREATE = """
mutation TransactionCreate(
    $id: ID!,
    $transaction: TransactionCreateInput!
    ){
    transactionCreate(
            id: $id,
            transaction: $transaction
        ){
        transaction{
            externalUrl
        }
        errors{
            field
            message
            code
        }
    }
}
"""

def test_transaction_create_with_absolute_external_url(
    order_with_lines, permission_manage_payments, app_api_client
):
    # given
    external_url = "https://example.com/success"
    variables = {
        "id": graphene.Node.to_global_id("Order", order_with_lines.pk),
        "transaction": {
            "name": "Credit Card",
            "externalUrl": external_url,
        },
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_CREATE, variables, permissions=[permission_manage_payments]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["transactionCreate"]
    assert not data["errors"]
    assert data["transaction"]["externalUrl"] == external_url

def test_transaction_create_with_relative_external_url(
    order_with_lines, permission_manage_payments, app_api_client
):
    # given
    external_url = "/success"
    variables = {
        "id": graphene.Node.to_global_id("Order", order_with_lines.pk),
        "transaction": {
            "name": "Credit Card",
            "externalUrl": external_url,
        },
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_CREATE, variables, permissions=[permission_manage_payments]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["transactionCreate"]
    assert not data["errors"]
    assert data["transaction"]["externalUrl"] == external_url
