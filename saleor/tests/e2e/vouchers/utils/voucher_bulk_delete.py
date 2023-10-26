from ...utils import get_graphql_content

VOUCHER_BULK_DELETE_MUTATION = """
mutation VoucherBulkDelete ($ids: [ID!]!) {
  voucherBulkDelete(ids: $ids) {
    errors {
      voucherCodes
      message
      field
      code
    }
    count
  }
}
"""


def voucher_bulk_delete(staff_api_client, voucher_ids):
    variables = {
        "ids": voucher_ids,
    }

    response = staff_api_client.post_graphql(
        VOUCHER_BULK_DELETE_MUTATION,
        variables,
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    data = content["data"]
    assert data["voucherBulkDelete"]["errors"] == []

    return data
