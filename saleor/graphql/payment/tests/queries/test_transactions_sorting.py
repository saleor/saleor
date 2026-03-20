from datetime import timedelta

import pytest
from django.utils import timezone

from .....payment.models import TransactionItem
from ....tests.utils import get_graphql_content
from ...sorters import TransactionSortField

TRANSACTIONS_SORT_QUERY = """
    query Transactions($sortBy: TransactionSortingInput){
        transactions(first: 10, sortBy: $sortBy) {
            edges {
                node {
                    id
                    pspReference
                }
            }
        }
    }
"""


@pytest.fixture
def transactions_with_different_dates(order_with_lines, transaction_item_generator):
    now = timezone.now()

    t_oldest = transaction_item_generator(
        order_id=order_with_lines.pk, psp_reference="OLDEST", currency="USD"
    )
    t_middle = transaction_item_generator(
        order_id=order_with_lines.pk, psp_reference="MIDDLE", currency="USD"
    )
    t_newest = transaction_item_generator(
        order_id=order_with_lines.pk, psp_reference="NEWEST", currency="USD"
    )

    oldest_date = now - timedelta(days=30)
    middle_date = now - timedelta(days=15)
    newest_date = now - timedelta(days=1)

    TransactionItem.objects.filter(pk=t_oldest.pk).update(
        created_at=oldest_date, modified_at=oldest_date
    )
    TransactionItem.objects.filter(pk=t_middle.pk).update(
        created_at=middle_date, modified_at=middle_date
    )
    TransactionItem.objects.filter(pk=t_newest.pk).update(
        created_at=newest_date, modified_at=newest_date
    )

    return t_oldest, t_middle, t_newest


def test_sort_by_created_at_asc(
    staff_api_client,
    permission_group_manage_orders,
    transactions_with_different_dates,
):
    # given
    t_oldest, t_middle, t_newest = transactions_with_different_dates
    staff_api_client.user.groups.add(permission_group_manage_orders)
    variables = {
        "sortBy": {"field": TransactionSortField.CREATED_AT.name, "direction": "ASC"}
    }

    # when
    response = staff_api_client.post_graphql(TRANSACTIONS_SORT_QUERY, variables)

    # then
    content = get_graphql_content(response)
    transactions = content["data"]["transactions"]["edges"]
    psp_refs = [t["node"]["pspReference"] for t in transactions]
    assert psp_refs == [
        t_oldest.psp_reference,
        t_middle.psp_reference,
        t_newest.psp_reference,
    ]


def test_sort_by_created_at_desc(
    staff_api_client,
    permission_group_manage_orders,
    transactions_with_different_dates,
):
    # given
    t_oldest, t_middle, t_newest = transactions_with_different_dates
    staff_api_client.user.groups.add(permission_group_manage_orders)
    variables = {
        "sortBy": {"field": TransactionSortField.CREATED_AT.name, "direction": "DESC"}
    }

    # when
    response = staff_api_client.post_graphql(TRANSACTIONS_SORT_QUERY, variables)

    # then
    content = get_graphql_content(response)
    transactions = content["data"]["transactions"]["edges"]
    psp_refs = [t["node"]["pspReference"] for t in transactions]
    assert psp_refs == [
        t_newest.psp_reference,
        t_middle.psp_reference,
        t_oldest.psp_reference,
    ]


def test_sort_by_modified_at_asc(
    staff_api_client,
    permission_group_manage_orders,
    transactions_with_different_dates,
):
    # given
    t_oldest, t_middle, t_newest = transactions_with_different_dates
    staff_api_client.user.groups.add(permission_group_manage_orders)
    variables = {
        "sortBy": {"field": TransactionSortField.MODIFIED_AT.name, "direction": "ASC"}
    }

    # when
    response = staff_api_client.post_graphql(TRANSACTIONS_SORT_QUERY, variables)

    # then
    content = get_graphql_content(response)
    transactions = content["data"]["transactions"]["edges"]
    psp_refs = [t["node"]["pspReference"] for t in transactions]
    assert psp_refs == [
        t_oldest.psp_reference,
        t_middle.psp_reference,
        t_newest.psp_reference,
    ]


def test_sort_by_modified_at_desc(
    staff_api_client,
    permission_group_manage_orders,
    transactions_with_different_dates,
):
    # given
    t_oldest, t_middle, t_newest = transactions_with_different_dates
    staff_api_client.user.groups.add(permission_group_manage_orders)
    variables = {
        "sortBy": {"field": TransactionSortField.MODIFIED_AT.name, "direction": "DESC"}
    }

    # when
    response = staff_api_client.post_graphql(TRANSACTIONS_SORT_QUERY, variables)

    # then
    content = get_graphql_content(response)
    transactions = content["data"]["transactions"]["edges"]
    psp_refs = [t["node"]["pspReference"] for t in transactions]
    assert psp_refs == [
        t_newest.psp_reference,
        t_middle.psp_reference,
        t_oldest.psp_reference,
    ]
