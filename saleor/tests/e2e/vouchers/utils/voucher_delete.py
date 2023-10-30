from ...utils import get_graphql_content

VOUCHER_DELETE_MUTATION = """
mutation VoucherDelete ($id: ID!) {
  voucherDelete(id: $id) {
    errors {
      message
      code
      field
      voucherCodes
    }
    voucher {
      id
    }
  }
}
"""


def voucher_delete(staff_api_client, voucher_id):
    variables = {
        "id": voucher_id,
    }

    response = staff_api_client.post_graphql(
        VOUCHER_DELETE_MUTATION,
        variables,
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    data = content["data"]["voucherDelete"]
    assert data["errors"] == []

    return data
