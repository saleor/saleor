from ...utils import get_graphql_content

VOUCHER_CODE_BULK_DELETE_MUTATION = """
mutation VoucherCodeBulkDelete ($ids: [ID!]!) {
  voucherCodeBulkDelete(ids: $ids) {
    errors {
      message
      code
      voucherCodes
    }
  }
}
"""


def voucher_code_bulk_delete(staff_api_client, voucher_code_ids):
    variables = {
        "ids": voucher_code_ids,
    }

    response = staff_api_client.post_graphql(
        VOUCHER_CODE_BULK_DELETE_MUTATION,
        variables,
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    data = content["data"]
    assert data["voucherCodeBulkDelete"]["errors"] == []

    return data
