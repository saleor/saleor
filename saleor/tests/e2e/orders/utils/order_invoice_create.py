from ...utils import get_graphql_content

ORDER_INVOICE_CREATE_MUTATION = """
mutation InvoiceCreate($id: ID!, $input: InvoiceCreateInput!){
  invoiceCreate(orderId: $id,
  input: $input,
  ) {
    errors {
      code
      field
      message
    }
    invoice {
      number
      url
      createdAt
      metadata{
        key
        value
      }
      privateMetadata{
        key
        value
      }
    }
  }
}
"""


def order_invoice_create(
    staff_api_client,
    order_id,
    input,
):
    variables = {
        "id": order_id,
        "input": input,
    }
    response = staff_api_client.post_graphql(
        ORDER_INVOICE_CREATE_MUTATION,
        variables=variables,
    )
    content = get_graphql_content(response)
    data = content["data"]["invoiceCreate"]
    assert data["errors"] == []

    return data
