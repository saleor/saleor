from ...utils import get_graphql_content

VOUCHER_CREATE_MUTATION = """
mutation VoucherCreate($input: VoucherInput!) {
  voucherCreate(input: $input) {
    errors {
      field
      message
      code
    }
    voucher {
      id
      startDate
      discountValueType
      type
      codes(first: 10) {
        edges {
          node {
            id
            code
            isActive
            used
          }
        }
        totalCount
      }
    }
  }
}
"""


def create_voucher(staff_api_client, input):
    variables = {
        "input": input,
    }

    response = staff_api_client.post_graphql(
        VOUCHER_CREATE_MUTATION,
        variables,
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    assert content["data"]["voucherCreate"]["errors"] == []

    data = content["data"]["voucherCreate"]["voucher"]
    assert data["id"] is not None

    return data
