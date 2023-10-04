import graphene
import pytest

from ....tests.utils import get_graphql_content

VOUCHER_CODE_BULK_DELETE_MUTATION = """
    mutation voucherCodeBulkDelete($ids: [ID!]!) {
        voucherCodeBulkDelete(ids: $ids) {
            count
        }
    }
"""


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_voucher_code_bulk_delete_queries(
    staff_api_client,
    permission_manage_discounts,
    voucher_with_many_codes,
    django_assert_num_queries,
    count_queries,
):
    # given
    codes = voucher_with_many_codes.codes.all()

    ids = [graphene.Node.to_global_id("VoucherCode", code.id) for code in codes]

    variables = {"ids": ids[:1]}

    # when
    with django_assert_num_queries(9):
        response = staff_api_client.post_graphql(
            VOUCHER_CODE_BULK_DELETE_MUTATION,
            variables,
            permissions=[permission_manage_discounts],
            check_no_permissions=False,
        )
        content = get_graphql_content(response)
        assert content["data"]["voucherCodeBulkDelete"]["count"] == 1

    variables = {"ids": ids[1:]}

    with django_assert_num_queries(9):
        response = staff_api_client.post_graphql(
            VOUCHER_CODE_BULK_DELETE_MUTATION,
            variables,
            permissions=[permission_manage_discounts],
            check_no_permissions=False,
        )
        content = get_graphql_content(response)
        assert content["data"]["voucherCodeBulkDelete"]["count"] == 4
