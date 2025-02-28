from ...utils import get_graphql_content

CUSTOMER_BULK_UPDATE_MUTATION = """
mutation CustomerBulkUpdate($errorPolicy: ErrorPolicyEnum, $customers: [CustomerBulkUpdateInput!]!) {
  customerBulkUpdate(errorPolicy: $errorPolicy, customers: $customers) {
    count
    results {
      customer {
        id
        email
        metadata {
          key
          value
        }
        privateMetadata {
          key
          value
        }
      }
      errors {
        path
        message
        code
      }
    }
    errors {
      path
      message
      code
    }
  }
}
"""


def customer_bulk_update(
    staff_api_client,
    customers,
    error_policy="REJECT_EVERYTHING",
):
    variables = {
        "customers": customers,
        "errorPolicy": error_policy,
    }

    response = staff_api_client.post_graphql(
        CUSTOMER_BULK_UPDATE_MUTATION,
        variables,
    )
    content = get_graphql_content(response)

    data = content["data"]["customerBulkUpdate"]

    return data
