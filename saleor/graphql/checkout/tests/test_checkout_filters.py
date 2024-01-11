import uuid
from datetime import date, timedelta
from decimal import Decimal

import graphene
import pytest
from django.core.exceptions import ValidationError
from freezegun import freeze_time
from prices import Money

from ....account.models import User
from ....checkout.models import Checkout
from ....checkout.payment_utils import update_checkout_payment_statuses
from ....payment.models import ChargeStatus, Payment
from ...core.connection import where_filter_qs
from ...tests.utils import get_graphql_content
from ..enums import CheckoutAuthorizeStatusEnum, CheckoutChargeStatusEnum
from ..filters import CheckoutDiscountedObjectWhere


@pytest.fixture
def checkout_query_with_filter():
    query = """
      query ($filter: CheckoutFilterInput!, ) {
        checkouts(first: 5, filter:$filter) {
          totalCount
          edges {
            node {
              id
            }
          }
        }
      }
    """
    return query


def test_checkout_query_with_filter_channels_with_one_channel(
    checkout_query_with_filter,
    staff_api_client,
    permission_manage_checkouts,
    checkouts_list,
    channel_USD,
):
    # given
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.pk)
    variables = {"filter": {"channels": [channel_id]}}

    # when
    response = staff_api_client.post_graphql(
        checkout_query_with_filter,
        variables,
        permissions=(permission_manage_checkouts,),
    )

    # then
    content = get_graphql_content(response)
    checkouts_list = content["data"]["checkouts"]["edges"]
    assert len(checkouts_list) == 3


def test_checkout_query_with_filter_channels_without_channel(
    checkout_query_with_filter,
    staff_api_client,
    permission_manage_checkouts,
    checkouts_list,
):
    # given
    variables = {"filter": {"channels": []}}

    # when
    response = staff_api_client.post_graphql(
        checkout_query_with_filter,
        variables,
        permissions=(permission_manage_checkouts,),
    )

    # then
    content = get_graphql_content(response)
    checkouts_list = content["data"]["checkouts"]["edges"]
    assert len(checkouts_list) == 5


def test_checkout_query_with_filter_channels_with_many_channel(
    checkout_query_with_filter,
    staff_api_client,
    permission_manage_checkouts,
    checkouts_list,
    channel_USD,
    channel_PLN,
    other_channel_USD,
):
    # given
    Checkout.objects.create(channel=other_channel_USD)
    channel_other_usd_id = graphene.Node.to_global_id("Channel", other_channel_USD.pk)
    channel_pln_id = graphene.Node.to_global_id("Channel", channel_PLN.pk)
    variables = {"filter": {"channels": [channel_pln_id, channel_other_usd_id]}}

    # when
    response = staff_api_client.post_graphql(
        checkout_query_with_filter,
        variables,
        permissions=(permission_manage_checkouts,),
    )

    # then
    content = get_graphql_content(response)
    checkout_list = content["data"]["checkouts"]["edges"]
    assert len(checkout_list) == 3


def test_checkout_query_with_filter_channels_with_empty_channel(
    checkout_query_with_filter,
    staff_api_client,
    permission_manage_checkouts,
    checkouts_list,
    other_channel_USD,
):
    # given
    channel_id = graphene.Node.to_global_id("Channel", other_channel_USD.pk)
    variables = {"filter": {"channels": [channel_id]}}

    # when
    response = staff_api_client.post_graphql(
        checkout_query_with_filter,
        variables,
        permissions=(permission_manage_checkouts,),
    )

    # then
    content = get_graphql_content(response)
    checkouts_list = content["data"]["checkouts"]["edges"]
    assert len(checkouts_list) == 0


@pytest.mark.parametrize(
    ("checkouts_filter", "count"),
    [
        (
            {
                "created": {
                    "gte": str(date.today() - timedelta(days=3)),
                    "lte": str(date.today()),
                }
            },
            1,
        ),
        ({"created": {"gte": str(date.today() - timedelta(days=3))}}, 1),
        ({"created": {"lte": str(date.today())}}, 2),
        ({"created": {"lte": str(date.today() - timedelta(days=3))}}, 1),
        ({"created": {"gte": str(date.today() + timedelta(days=1))}}, 0),
    ],
)
def test_checkout_query_with_filter_created(
    checkouts_filter,
    count,
    checkout_query_with_filter,
    staff_api_client,
    permission_manage_checkouts,
    channel_USD,
):
    Checkout.objects.create(channel=channel_USD)
    with freeze_time("2012-01-14"):
        Checkout.objects.create(channel=channel_USD)
    variables = {"filter": checkouts_filter}
    staff_api_client.user.user_permissions.add(permission_manage_checkouts)
    response = staff_api_client.post_graphql(checkout_query_with_filter, variables)
    content = get_graphql_content(response)
    checkouts_list = content["data"]["checkouts"]["edges"]

    assert len(checkouts_list) == count


@pytest.mark.parametrize(
    ("checkouts_filter", "user_field", "user_value"),
    [
        ({"customer": "admin"}, "email", "admin@example.com"),
        ({"customer": "John"}, "first_name", "johnny"),
        ({"customer": "Snow"}, "last_name", "snow"),
    ],
)
def test_checkouts_query_with_filter_customer_fields(
    checkouts_filter,
    user_field,
    user_value,
    checkout_query_with_filter,
    staff_api_client,
    permission_manage_checkouts,
    customer_user,
    channel_USD,
):
    setattr(customer_user, user_field, user_value)
    customer_user.save()
    customer_user.refresh_from_db()

    checkout = Checkout(
        user=customer_user, token=str(uuid.uuid4()), channel=channel_USD
    )
    Checkout.objects.bulk_create(
        [checkout, Checkout(token=str(uuid.uuid4()), channel=channel_USD)]
    )

    variables = {"filter": checkouts_filter}
    staff_api_client.user.user_permissions.add(permission_manage_checkouts)
    response = staff_api_client.post_graphql(checkout_query_with_filter, variables)
    content = get_graphql_content(response)
    checkout_list = content["data"]["checkouts"]["edges"]
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    assert len(checkout_list) == 1
    assert checkout_list[0]["node"]["id"] == checkout_id


QUERY_CHECKOUT_WITH_SORT = """
    query ($sort_by: CheckoutSortingInput!) {
        checkouts(first:5, sortBy: $sort_by) {
            edges{
                node{
                    token
                }
            }
        }
    }
"""


@pytest.mark.parametrize(
    ("checkout_sort", "result_order"),
    [
        ({"field": "CREATION_DATE", "direction": "ASC"}, [1, 0, 2]),
        ({"field": "CREATION_DATE", "direction": "DESC"}, [2, 0, 1]),
        ({"field": "CUSTOMER", "direction": "ASC"}, [2, 0, 1]),
        ({"field": "CUSTOMER", "direction": "DESC"}, [1, 0, 2]),
        ({"field": "PAYMENT", "direction": "ASC"}, [0, 1, 2]),
        ({"field": "PAYMENT", "direction": "DESC"}, [2, 1, 0]),
    ],
)
def test_query_checkout_with_sort(
    checkout_sort,
    result_order,
    staff_api_client,
    permission_manage_checkouts,
    address,
    channel_USD,
):
    created_checkouts = []
    with freeze_time("2017-01-14"):
        created_checkouts.append(
            Checkout.objects.create(
                token=str(uuid.uuid4()),
                billing_address=address,
                channel=channel_USD,
            )
        )
    with freeze_time("2012-01-14"):
        address2 = address.get_copy()
        address2.first_name = "Walter"
        address2.save()
        created_checkouts.append(
            Checkout.objects.create(
                token=str(uuid.uuid4()),
                billing_address=address2,
                channel=channel_USD,
            )
        )
    address3 = address.get_copy()
    address3.last_name = "Alice"
    address3.save()
    created_checkouts.append(
        Checkout.objects.create(
            token=str(uuid.uuid4()),
            billing_address=address3,
            channel=channel_USD,
        )
    )

    Payment.objects.create(
        checkout=created_checkouts[0], charge_status=ChargeStatus.FULLY_CHARGED
    )

    Payment.objects.create(
        checkout=created_checkouts[1], charge_status=ChargeStatus.NOT_CHARGED
    )

    variables = {"sort_by": checkout_sort}
    staff_api_client.user.user_permissions.add(permission_manage_checkouts)
    response = staff_api_client.post_graphql(QUERY_CHECKOUT_WITH_SORT, variables)
    content = get_graphql_content(response)
    checkouts = content["data"]["checkouts"]["edges"]

    for checkout, checkout_number in enumerate(result_order):
        assert checkouts[checkout]["node"]["token"] == str(
            created_checkouts[checkout_number].pk
        )


@pytest.mark.parametrize(
    ("checkouts_filter", "count"),
    [
        ({"search": "user_email"}, 2),
        ({"search": "john@wayne.com"}, 1),
        ({"search": "Leslie"}, 1),
        ({"search": "Wade"}, 1),
        ({"search": ""}, 4),
        ({"search": "ExternalID"}, 1),
    ],
)
def test_checkouts_query_with_filter_search(
    checkouts_filter,
    count,
    checkout_query_with_filter,
    staff_api_client,
    permission_manage_checkouts,
    customer_user,
    channel_USD,
):
    user1 = User.objects.create(email="user_email1@example.com")
    user2 = User.objects.create(email="user_email2@example.com")
    user3 = User.objects.create(email="john@wayne.com")

    checkouts = Checkout.objects.bulk_create(
        [
            Checkout(
                user=customer_user,
                token=str(uuid.uuid4()),
                channel=channel_USD,
            ),
            Checkout(
                token=str(uuid.uuid4()),
                user=user1,
                channel=channel_USD,
            ),
            Checkout(
                token=str(uuid.uuid4()),
                user=user2,
                channel=channel_USD,
            ),
            Checkout(
                token=str(uuid.uuid4()),
                user=user3,
                channel=channel_USD,
            ),
        ]
    )

    checkout_with_payment = checkouts[1]
    payment = Payment.objects.create(
        checkout=checkout_with_payment, psp_reference="ExternalID"
    )
    payment.transactions.create(gateway_response={}, is_success=True)
    variables = {"filter": checkouts_filter}
    staff_api_client.user.user_permissions.add(permission_manage_checkouts)
    response = staff_api_client.post_graphql(checkout_query_with_filter, variables)
    content = get_graphql_content(response)

    assert content["data"]["checkouts"]["totalCount"] == count


def test_checkouts_query_with_filter_search_by_global_payment_id(
    checkout_query_with_filter,
    staff_api_client,
    permission_manage_checkouts,
    customer_user,
    channel_USD,
):
    checkouts = Checkout.objects.bulk_create(
        [
            Checkout(
                user=customer_user,
                token=str(uuid.uuid4()),
                channel=channel_USD,
            ),
            Checkout(
                token=str(uuid.uuid4()),
                channel=channel_USD,
                user=User.objects.create(email="user1@example.com"),
            ),
        ]
    )

    checkout_with_payment = checkouts[0]
    payment = Payment.objects.create(checkout=checkout_with_payment)
    global_id = graphene.Node.to_global_id("Payment", payment.pk)

    variables = {"filter": {"search": global_id}}
    staff_api_client.user.user_permissions.add(permission_manage_checkouts)
    response = staff_api_client.post_graphql(checkout_query_with_filter, variables)
    content = get_graphql_content(response)
    assert content["data"]["checkouts"]["totalCount"] == 1


def test_checkouts_query_with_filter_search_by_token(
    checkout_query_with_filter, checkout, staff_api_client, permission_manage_checkouts
):
    variables = {"filter": {"search": checkout.pk}}
    staff_api_client.user.user_permissions.add(permission_manage_checkouts)
    response = staff_api_client.post_graphql(checkout_query_with_filter, variables)
    content = get_graphql_content(response)
    assert content["data"]["checkouts"]["totalCount"] == 1


@pytest.mark.parametrize(
    ("transaction_data", "statuses", "expected_count"),
    [
        (
            {"authorized_value": Decimal("10")},
            [CheckoutAuthorizeStatusEnum.PARTIAL.name],
            1,
        ),
        (
            {"charged_value": Decimal("10")},
            [CheckoutAuthorizeStatusEnum.PARTIAL.name],
            1,
        ),
        (
            {"authorize_pending_value": Decimal("10")},
            [CheckoutAuthorizeStatusEnum.PARTIAL.name],
            1,
        ),
        (
            {"charge_pending_value": Decimal("10")},
            [CheckoutAuthorizeStatusEnum.PARTIAL.name],
            1,
        ),
        (
            {"authorized_value": Decimal("0")},
            [CheckoutAuthorizeStatusEnum.NONE.name],
            1,
        ),
        (
            {"authorized_value": Decimal("200")},
            [CheckoutAuthorizeStatusEnum.FULL.name],
            2,
        ),
        (
            {"charged_value": Decimal("200")},
            [CheckoutAuthorizeStatusEnum.FULL.name],
            2,
        ),
        (
            {"authorize_pending_value": Decimal("200")},
            [CheckoutAuthorizeStatusEnum.FULL.name],
            2,
        ),
        (
            {"charge_pending_value": Decimal("200")},
            [CheckoutAuthorizeStatusEnum.FULL.name],
            2,
        ),
        (
            {"authorized_value": Decimal("10")},
            [
                CheckoutAuthorizeStatusEnum.FULL.name,
                CheckoutAuthorizeStatusEnum.PARTIAL.name,
            ],
            2,
        ),
        (
            {"authorized_value": Decimal("0")},
            [
                CheckoutAuthorizeStatusEnum.FULL.name,
                CheckoutAuthorizeStatusEnum.NONE.name,
            ],
            2,
        ),
        (
            {"authorized_value": Decimal("10"), "charged_value": Decimal("90")},
            [CheckoutAuthorizeStatusEnum.PARTIAL.name],
            1,
        ),
    ],
)
def test_checkouts_query_with_filter_authorize_status(
    transaction_data,
    statuses,
    expected_count,
    checkout_query_with_filter,
    staff_api_client,
    permission_manage_checkouts,
    customer_user,
    channel_USD,
    checkout_with_prices,
    checkout,
):
    # given
    first_checkout = Checkout.objects.create(
        currency=channel_USD.currency_code, channel=channel_USD
    )
    first_checkout.payment_transactions.create(
        currency=checkout_with_prices.currency, authorized_value=Decimal("10")
    )

    update_checkout_payment_statuses(
        first_checkout, first_checkout.total.gross, checkout_has_lines=True
    )

    checkout_with_prices.payment_transactions.create(
        currency=checkout_with_prices.currency, **transaction_data
    )
    update_checkout_payment_statuses(
        checkout_with_prices, checkout_with_prices.total.gross, checkout_has_lines=True
    )

    variables = {"filter": {"authorizeStatus": statuses}}
    staff_api_client.user.user_permissions.add(permission_manage_checkouts)

    # when
    response = staff_api_client.post_graphql(checkout_query_with_filter, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["checkouts"]["totalCount"] == expected_count


@pytest.mark.parametrize(
    ("transaction_data", "statuses", "expected_count"),
    [
        (
            {"charged_value": Decimal("10")},
            [CheckoutChargeStatusEnum.PARTIAL.name],
            1,
        ),
        (
            {"charge_pending_value": Decimal("10")},
            [CheckoutChargeStatusEnum.PARTIAL.name],
            1,
        ),
        (
            {"charged_value": Decimal("00")},
            [CheckoutChargeStatusEnum.PARTIAL.name],
            0,
        ),
        (
            {"charged_value": Decimal("178.00")},
            [CheckoutChargeStatusEnum.FULL.name],
            1,
        ),
        (
            {"charge_pending_value": Decimal("178.00")},
            [CheckoutChargeStatusEnum.FULL.name],
            1,
        ),
        (
            {
                "charge_pending_value": Decimal("100.00"),
                "charged_value": Decimal("78.00"),
            },
            [CheckoutChargeStatusEnum.FULL.name],
            1,
        ),
        (
            {"charged_value": Decimal("0.00")},
            [CheckoutChargeStatusEnum.OVERCHARGED.name],
            1,
        ),
        (
            {"charged_value": Decimal("10")},
            [CheckoutChargeStatusEnum.FULL.name, CheckoutChargeStatusEnum.PARTIAL.name],
            1,
        ),
        (
            {"charged_value": Decimal("0")},
            [CheckoutChargeStatusEnum.FULL.name, CheckoutChargeStatusEnum.NONE.name],
            1,
        ),
        (
            {"charged_value": Decimal("178.00")},
            [
                CheckoutChargeStatusEnum.FULL.name,
                CheckoutChargeStatusEnum.OVERCHARGED.name,
            ],
            2,
        ),
    ],
)
def test_checkouts_query_with_filter_charge_status(
    transaction_data,
    statuses,
    expected_count,
    checkout_query_with_filter,
    checkout_with_prices,
    staff_api_client,
    permission_manage_checkouts,
    customer_user,
    channel_USD,
):
    # given
    first_checkout = Checkout.objects.create(
        currency=channel_USD.currency_code, channel=channel_USD
    )
    first_checkout.payment_transactions.create(
        currency=checkout_with_prices.currency, charged_value=Decimal("10")
    )

    update_checkout_payment_statuses(
        first_checkout, first_checkout.total.gross, checkout_has_lines=True
    )

    checkout_with_prices.payment_transactions.create(
        currency=checkout_with_prices.currency, **transaction_data
    )
    update_checkout_payment_statuses(
        checkout_with_prices, checkout_with_prices.total.gross, checkout_has_lines=True
    )

    variables = {"filter": {"chargeStatus": statuses}}
    staff_api_client.user.user_permissions.add(permission_manage_checkouts)

    # when
    response = staff_api_client.post_graphql(checkout_query_with_filter, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["checkouts"]["totalCount"] == expected_count


def test_filtering_checkout_discounted_object_where_by_base_total_price_range(
    checkout_with_item,
):
    # given
    checkout = checkout_with_item

    currency = checkout.currency
    subtotal_price = Money("20", currency)
    total_price = Money("30", currency)
    checkout.base_total = total_price
    checkout.base_subtotal = subtotal_price
    checkout.save(update_fields=["base_total_amount", "base_subtotal_amount"])

    Checkout.objects.create(
        currency=currency,
        user=checkout.user,
        channel=checkout.channel,
        base_total=Money("15", currency),
        base_subtotal=Money("10", currency),
    )

    qs = Checkout.objects.all()
    predicate_data = {
        "currency": currency,
        "base_total_price": {
            "range": {
                "gte": 20,
            }
        },
    }

    # when
    result = where_filter_qs(
        qs,
        {},
        CheckoutDiscountedObjectWhere,
        predicate_data,
        None,
    )

    # then
    assert result.count() == 1
    assert result.first() == checkout


def test_filtering_checkout_discounted_object_where_by_base_total_price_one_of(
    checkout_with_item,
):
    # given
    checkout = checkout_with_item

    currency = checkout.currency
    subtotal_price = Money("20", currency)
    total_price = Money("30", currency)
    checkout.base_total = total_price
    checkout.base_subtotal = subtotal_price
    checkout.save(update_fields=["base_total_amount", "base_subtotal_amount"])

    another_checkout = Checkout.objects.create(
        currency=currency,
        user=checkout.user,
        channel=checkout.channel,
        base_total=Money("15", currency),
        base_subtotal=Money("10", currency),
    )

    qs = Checkout.objects.all()
    predicate_data = {"currency": currency, "base_total_price": {"one_of": [15, 40]}}

    # when
    result = where_filter_qs(
        qs,
        {},
        CheckoutDiscountedObjectWhere,
        predicate_data,
        None,
    )

    # then
    assert result.count() == 1
    assert result.first() == another_checkout


def test_filtering_checkout_discounted_object_where_by_base_total_currency_not_given(
    checkout_with_item,
):
    # given
    checkout = checkout_with_item

    currency = checkout.currency
    subtotal_price = Money("20", currency)
    total_price = Money("30", currency)
    checkout.base_total = total_price
    checkout.base_subtotal = subtotal_price
    checkout.save(update_fields=["base_total_amount", "base_subtotal_amount"])

    Checkout.objects.create(
        currency=currency,
        user=checkout.user,
        channel=checkout.channel,
        base_total=Money("15", currency),
        base_subtotal=Money("10", currency),
    )

    qs = Checkout.objects.all()
    predicate_data = {
        "base_total_price": {
            "range": {
                "gte": 20,
            }
        }
    }

    # when
    with pytest.raises(ValidationError) as validation_error:
        where_filter_qs(
            qs,
            {},
            CheckoutDiscountedObjectWhere,
            predicate_data,
            None,
        )

    # then
    assert validation_error.value.code == "required"


def test_filtering_checkout_discounted_object_where_by_base_subtotal_price_range(
    checkout_with_item,
):
    # given
    checkout = checkout_with_item

    currency = checkout.currency
    subtotal_price = Money("20", currency)
    total_price = Money("30", currency)
    checkout.base_total = total_price
    checkout.base_subtotal = subtotal_price
    checkout.save(update_fields=["base_total_amount", "base_subtotal_amount"])

    another_checkout = Checkout.objects.create(
        currency=currency,
        user=checkout.user,
        channel=checkout.channel,
        base_total=Money("15", currency),
        base_subtotal=Money("10", currency),
    )

    qs = Checkout.objects.all()
    predicate_data = {
        "currency": currency,
        "base_subtotal_price": {
            "range": {
                "lte": 12,
            }
        },
    }

    # when
    result = where_filter_qs(
        qs,
        {},
        CheckoutDiscountedObjectWhere,
        predicate_data,
        None,
    )

    # then
    assert result.count() == 1
    assert result.first() == another_checkout


def test_filtering_checkout_discounted_object_where_by_base_subtotal_price_one_of(
    checkout_with_item,
):
    # given
    checkout = checkout_with_item

    currency = checkout.currency
    subtotal_price = Money("20", currency)
    total_price = Money("30", currency)
    checkout.base_total = total_price
    checkout.base_subtotal = subtotal_price
    checkout.save(update_fields=["base_total_amount", "base_subtotal_amount"])

    Checkout.objects.create(
        currency=currency,
        user=checkout.user,
        channel=checkout.channel,
        base_total=Money("15", currency),
        base_subtotal=Money("10", currency),
    )

    qs = Checkout.objects.all()
    predicate_data = {"currency": currency, "base_subtotal_price": {"one_of": [15, 20]}}

    # when
    result = where_filter_qs(
        qs,
        {},
        CheckoutDiscountedObjectWhere,
        predicate_data,
        None,
    )

    # then
    assert result.count() == 1
    assert result.first() == checkout


def test_filtering_checkout_discounted_object_where_by_base_subtotal_currency_not_given(
    checkout_with_item,
):
    # given
    checkout = checkout_with_item

    currency = checkout.currency
    subtotal_price = Money("20", currency)
    total_price = Money("30", currency)
    checkout.base_total = total_price
    checkout.base_subtotal = subtotal_price
    checkout.save(update_fields=["base_total_amount", "base_subtotal_amount"])

    Checkout.objects.create(
        currency=currency,
        user=checkout.user,
        channel=checkout.channel,
        base_total=Money("15", currency),
        base_subtotal=Money("10", currency),
    )

    qs = Checkout.objects.all()
    predicate_data = {
        "base_subtotal_price": {
            "range": {
                "gte": 20,
            }
        }
    }

    # when
    with pytest.raises(ValidationError) as validation_error:
        where_filter_qs(
            qs,
            {},
            CheckoutDiscountedObjectWhere,
            predicate_data,
            None,
        )

    # then
    assert validation_error.value.code == "required"
