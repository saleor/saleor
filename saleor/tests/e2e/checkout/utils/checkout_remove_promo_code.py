from ...utils import get_graphql_content

CHECKOUT_REMOVE_PROMO_CODE_MUTATION = """
mutation CheckoutRemovePromoCode($id: ID, $promoCode: String) {
    checkoutRemovePromoCode(
        id: $id
        promoCode: $promoCode
    ) {
        errors {
            message
            field
            code
        }
        checkout {
            id
            voucherCode
            totalPrice {
                gross {
                    amount
                    }
                }
        }
    }
}
"""


def checkout_remove_promo_code(api_client, checkout_id, voucher_code):
    variables = {
        "id": checkout_id,
        "promoCode": voucher_code,
    }

    response = api_client.post_graphql(
        CHECKOUT_REMOVE_PROMO_CODE_MUTATION,
        variables=variables,
    )
    content = get_graphql_content(response)

    data = content["data"]["checkoutRemovePromoCode"]
    assert data["errors"] == []

    return data
