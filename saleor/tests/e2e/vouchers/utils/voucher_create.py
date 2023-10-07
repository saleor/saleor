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
    }
  }
}
"""


def create_voucher(
    staff_api_client,
    discountValueType,
    code,
    type="ENTIRE_ORDER",
    only_for_staff=False,
):
    variables = {
        "input": {
            "code": code,
            "discountValueType": discountValueType,
            "type": type,
            "onlyForStaff": only_for_staff,
        }
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
    assert data["startDate"] is not None
    assert data["discountValueType"] == discountValueType
    assert data["type"] == type

    return data
