from ...utils import get_graphql_content

VOUCHER_QUERY = """
query voucherQuery ($id:ID!){
  voucher(id: $id) {
    discountValue
    discountValueType
    id
    name
    onlyForStaff
    singleUse
    startDate
    endDate
    used
    usageLimit
    codes(first: 10) {
      edges {
        node {
          code
          id
          isActive
          used
        }
      }
    }
  }
}
"""


def get_voucher(
    api_client,
    voucher_id,
):
    variables = {"id": voucher_id}

    response = api_client.post_graphql(VOUCHER_QUERY, variables)
    content = get_graphql_content(response)

    return content["data"]
