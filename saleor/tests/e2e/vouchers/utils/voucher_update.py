from ...utils import get_graphql_content

VOUCHER_UPDATE_MUTATION = """
mutation VoucherUpdate($id:ID! $input: VoucherInput!) {
  voucherUpdate(id: $id, input: $input) {
    errors {
      message
      code
      field
    }
    voucher {
      id
      applyOncePerCustomer
      applyOncePerOrder
      endDate
      onlyForStaff
      startDate
      type
      usageLimit
      used
      minCheckoutItemsQuantity
      minSpent {
        amount
      }
      code
      discountValueType
      discountValue
    }
  }
}
"""


def raw_update_voucher(staff_api_client, voucher_id, input_data):
    variables = {
        "id": voucher_id,
        "input": input_data,
    }

    response = staff_api_client.post_graphql(
        VOUCHER_UPDATE_MUTATION,
        variables,
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    data = content["data"]["voucherUpdate"]

    return data


def update_voucher(staff_api_client, voucher_id, input_data):
    response = raw_update_voucher(staff_api_client, voucher_id, input_data)

    assert response["errors"] == []
    data = response["voucher"]
    assert data["id"] is not None

    return data
