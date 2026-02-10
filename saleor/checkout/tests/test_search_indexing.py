from decimal import Decimal
from unittest.mock import patch

import graphene
import pytest

from ...payment.models import Payment, TransactionEvent, TransactionItem
from ...plugins.manager import get_plugins_manager
from ...tests import race_condition
from ..fetch import fetch_checkout_info
from ..models import Checkout, CheckoutMetadata
from ..search.indexing import (
    generate_checkout_lines_search_vector_value,
    generate_checkout_payments_search_vector_value,
    generate_checkout_transactions_search_vector_value,
    prepare_checkout_search_vector_value,
    search_checkouts,
    update_checkouts_search_vector,
)
from ..search.loaders import (
    CheckoutData,
    CheckoutLineData,
    TransactionData,
)
from ..utils import add_variant_to_checkout


@pytest.fixture
def checkout_list_with_relations(
    channel_USD, customer_user, address, address_usa, product
):
    """Create multiple checkouts with various relations for testing."""

    checkouts = []
    variant = product.variants.first()

    for i in range(3):
        checkout = Checkout.objects.create(
            currency=channel_USD.currency_code,
            channel=channel_USD,
            email=f"user{i}@example.com",
            user=customer_user if i % 2 == 0 else None,
            billing_address=address if i % 2 == 0 else None,
            shipping_address=address_usa if i % 2 == 1 else None,
        )
        checkout.set_country("US", commit=True)
        CheckoutMetadata.objects.create(checkout=checkout)

        # Add checkout line
        checkout_info = fetch_checkout_info(
            checkout, [], get_plugins_manager(allow_replica=False)
        )
        add_variant_to_checkout(checkout_info, variant, i + 1)
        checkout.save()

        # Add payment
        Payment.objects.create(
            gateway="mirumee.payments.dummy",
            is_active=True,
            checkout=checkout,
            total=Decimal("10.00") * (i + 1),
            currency="USD",
            psp_reference=f"PSP-REF-{i}",
        )

        # Add transaction
        transaction = TransactionItem.objects.create(
            name="Credit card",
            psp_reference=f"TRANS-PSP-{i}",
            available_actions=["refund"],
            currency="USD",
            checkout_id=checkout.pk,
            charged_value=Decimal(10) * (i + 1),
        )
        TransactionEvent.objects.create(
            psp_reference=f"EVENT-PSP-{i}",
            currency="USD",
            transaction=transaction,
            amount_value=Decimal(10),
        )

        checkouts.append(checkout)

    return checkouts


def _extract_search_vector_values(search_vectors):
    """Extract values from NoValidationSearchVector objects."""
    values = []
    for sv in search_vectors:
        if hasattr(sv, "source_expressions") and sv.source_expressions:
            expr = sv.source_expressions[0]
            if hasattr(expr, "value"):
                values.append(str(expr.value))
    return values


def test_update_checkouts_search_vector(checkout_with_item):
    # given
    checkout = checkout_with_item
    assert not checkout.search_vector

    # when
    update_checkouts_search_vector([checkout])

    # then
    checkout.refresh_from_db()
    assert checkout.search_vector
    assert checkout.search_index_dirty is False


def test_update_checkouts_search_vector_multiple_checkouts(
    checkout_with_item, checkout
):
    # given
    assert not checkout_with_item.search_vector
    assert not checkout.search_vector

    # when
    update_checkouts_search_vector([checkout_with_item, checkout])

    # then
    checkout_with_item.refresh_from_db()
    checkout.refresh_from_db()
    assert checkout_with_item.search_vector
    assert checkout_with_item.search_index_dirty is False
    assert checkout.search_vector
    assert checkout.search_index_dirty is False


def test_update_checkouts_search_vector_empty_list(db):
    # given
    checkouts = []

    # when/then - should not raise any errors
    update_checkouts_search_vector(checkouts)


def test_update_checkouts_search_vector_constant_queries(
    checkout_list_with_relations, django_assert_num_queries
):
    """Ensure that data loaders are working correctly and number of db queries is constant."""
    # given
    checkout_list = checkout_list_with_relations

    # when & then
    # Expected query breakdown (14 total):
    # First transaction block:
    # 1. Select for update (filter dirty checkouts)
    # 2. Update search_index_dirty flag
    # Load checkout data:
    # 3. Load users (1 query)
    # 4. Load addresses (1 query)
    # 5. Load payments (1 query)
    # 6. Load checkout lines (1 query)
    # 7. Load transactions (1 query)
    # 8. Load product variants (1 query)
    # 9. Load products (1 query)
    # 10. Load transaction events (1 query)
    # Second transaction block:
    # 11. Transaction savepoint
    # 12. Select for update (lock checkouts)
    # 13. Bulk update search vectors
    # 14. Release savepoint

    expected_queries = 14
    with django_assert_num_queries(expected_queries):
        update_checkouts_search_vector(checkout_list[: len(checkout_list) - 1])
    with django_assert_num_queries(expected_queries):
        update_checkouts_search_vector(checkout_list)


def test_prepare_checkout_search_vector_value_basic(checkout):
    # given
    checkout.email = "test@example.com"
    checkout.save(update_fields=["email"])
    data = CheckoutData(
        user=None,
        billing_address=None,
        shipping_address=None,
        payments=[],
        lines=[],
        transactions=[],
    )

    # when
    search_vectors = prepare_checkout_search_vector_value(checkout, data)

    # then
    search_vector_values = _extract_search_vector_values(search_vectors)
    assert str(checkout.token) in search_vector_values
    assert checkout.email in search_vector_values


def test_prepare_checkout_search_vector_value_with_user(checkout, customer_user):
    # given
    checkout.user = customer_user
    checkout.email = "test@example.com"
    checkout.save(update_fields=["user", "email"])

    data = CheckoutData(
        user=customer_user,
        billing_address=None,
        shipping_address=None,
        payments=[],
        lines=[],
        transactions=[],
    )

    # when
    search_vectors = prepare_checkout_search_vector_value(checkout, data)

    # then
    search_vector_values = _extract_search_vector_values(search_vectors)
    assert str(checkout.token) in search_vector_values
    assert checkout.email in search_vector_values
    assert customer_user.email in search_vector_values
    assert customer_user.first_name in search_vector_values
    assert customer_user.last_name in search_vector_values


def test_prepare_checkout_search_vector_value_with_addresses(
    checkout, address, address_usa
):
    # given
    checkout.billing_address = address
    checkout.shipping_address = address_usa
    checkout.save(update_fields=["billing_address", "shipping_address"])

    data = CheckoutData(
        user=None,
        billing_address=address,
        shipping_address=address_usa,
        payments=[],
        lines=[],
        transactions=[],
    )

    # when
    search_vectors = prepare_checkout_search_vector_value(checkout, data)

    # then
    search_vector_values = _extract_search_vector_values(search_vectors)
    assert str(checkout.token) in search_vector_values
    # Check billing address data is included
    assert address.city in search_vector_values
    # Check shipping address data is included
    assert address_usa.city in search_vector_values


def test_prepare_checkout_search_vector_value_with_no_email(checkout):
    # given
    checkout.email = None
    checkout.save(update_fields=["email"])

    data = CheckoutData(
        user=None,
        billing_address=None,
        shipping_address=None,
        payments=[],
        lines=[],
        transactions=[],
    )

    # when
    search_vectors = prepare_checkout_search_vector_value(checkout, data)

    # then
    assert len(search_vectors) == 1
    search_vector_values = _extract_search_vector_values(search_vectors)
    assert str(checkout.token) in search_vector_values


def test_generate_checkout_payments_search_vector_value_empty():
    # given
    payments = []

    # when
    result = generate_checkout_payments_search_vector_value(payments)

    # then
    assert result == []


def test_generate_checkout_payments_search_vector_value(checkout):
    # given
    psp_ref_1 = "PSP-REF-123"
    psp_ref_2 = "PSP-REF-456"

    payment1 = Payment.objects.create(
        gateway="mirumee.payments.dummy",
        is_active=True,
        checkout=checkout,
        total=Decimal("10.00"),
        currency="USD",
        psp_reference=psp_ref_1,
    )
    payment2 = Payment.objects.create(
        gateway="mirumee.payments.dummy",
        is_active=False,
        checkout=checkout,
        total=Decimal("20.00"),
        currency="USD",
        psp_reference=psp_ref_2,
    )
    payments = [payment1, payment2]

    # when
    result = generate_checkout_payments_search_vector_value(payments)

    # then
    assert len(result) == 4
    search_vector_values = _extract_search_vector_values(result)
    assert psp_ref_1 in search_vector_values
    assert (
        str(graphene.Node.to_global_id("Payment", payment1.id)) in search_vector_values
    )
    assert psp_ref_2 in search_vector_values
    assert (
        str(graphene.Node.to_global_id("Payment", payment2.id)) in search_vector_values
    )


def test_generate_checkout_payments_search_vector_value_respects_max_limit(
    checkout, settings
):
    # given
    limit = 5
    settings.CHECKOUT_MAX_INDEXED_PAYMENTS = limit
    payments = []
    for i in range(limit + 50):
        payments.append(
            Payment(
                gateway="mirumee.payments.dummy",
                is_active=True,
                checkout=checkout,
                total=Decimal("10.00"),
                currency="USD",
                psp_reference=f"PSP-REF-{i}",
            )
        )
    Payment.objects.bulk_create(payments)

    # when
    result = generate_checkout_payments_search_vector_value(payments)

    # then
    assert len(result) == limit * 2  # IDs + psp_references


def test_generate_checkout_lines_search_vector_value_empty():
    # given
    lines = []

    # when
    result = generate_checkout_lines_search_vector_value(lines)

    # then
    assert result == []


def test_generate_checkout_lines_search_vector_value(checkout_with_item, product):
    # given
    sku = "TEST-SKU-123"
    line = checkout_with_item.lines.first()
    variant = line.variant
    variant.sku = sku
    variant.save(update_fields=["sku"])

    line_data = CheckoutLineData(
        line=line,
        variant=variant,
        product=product,
    )

    # when
    result = generate_checkout_lines_search_vector_value([line_data])

    # then
    assert result
    search_vector_values = _extract_search_vector_values(result)
    assert sku in search_vector_values
    assert product.name in search_vector_values


def test_generate_checkout_lines_search_vector_value_without_variant(
    checkout_with_item,
):
    # given
    line = checkout_with_item.lines.first()
    line_data = CheckoutLineData(
        line=line,
        variant=None,
        product=None,
    )

    # when
    result = generate_checkout_lines_search_vector_value([line_data])

    # then
    assert result == []


def test_generate_checkout_lines_search_vector_value_without_sku(
    checkout_with_item, product
):
    # given
    line = checkout_with_item.lines.first()
    variant = line.variant
    variant.sku = None
    variant.save()

    line_data = CheckoutLineData(
        line=line,
        variant=variant,
        product=product,
    )

    # when
    result = generate_checkout_lines_search_vector_value([line_data])

    # then
    assert len(result) == 1
    search_vector_values = _extract_search_vector_values(result)
    assert product.name in search_vector_values
    # Variant name may be empty, only check if it's not empty
    if variant.name:
        assert variant.name in search_vector_values


def test_generate_checkout_lines_search_vector_value_respects_max_limit(
    checkout, product, settings
):
    # given
    variant = product.variants.first()
    variant.name = "variant name"
    variant.sku = "variant-sku-001"
    variant.save(update_fields=["name", "sku"])

    product.name = "product name"
    product.save(update_fields=["name"])

    limit = 10
    settings.CHECKOUT_MAX_INDEXED_LINES = limit

    lines_data = []
    for _ in range(limit + 50):
        line_data = CheckoutLineData(
            line=checkout.lines.first(),  # Use actual line instead of None
            variant=variant,
            product=product,
        )
        lines_data.append(line_data)

    # when
    result = generate_checkout_lines_search_vector_value(lines_data)

    # then
    # Should respect limit (10)
    # Each line can have up to 3 vectors (SKU, product name, variant name)
    assert len(result) == limit * 3


def test_generate_checkout_transactions_search_vector_value_empty():
    # given
    transactions = []

    # when
    result = generate_checkout_transactions_search_vector_value(transactions)

    # then
    assert result == []


def test_generate_checkout_transactions_search_vector_value(checkout):
    # given
    transaction_psp_ref = "PSP-TRANS-123"
    event_psp_ref = "EVENT-PSP-123"

    transaction = TransactionItem.objects.create(
        name="Credit card",
        psp_reference=transaction_psp_ref,
        available_actions=["refund"],
        currency="USD",
        checkout_id=checkout.pk,
        charged_value=Decimal(10),
    )
    event = TransactionEvent.objects.create(
        psp_reference=event_psp_ref,
        currency="USD",
        transaction=transaction,
        amount_value=Decimal(10),
    )

    transaction_data = TransactionData(
        transaction=transaction,
        events=[event],
    )

    # when
    result = generate_checkout_transactions_search_vector_value([transaction_data])

    # then
    assert len(result) == 3
    search_vector_values = _extract_search_vector_values(result)
    assert transaction_psp_ref in search_vector_values
    assert event_psp_ref in search_vector_values


def test_generate_checkout_transactions_search_vector_value_without_psp_reference(
    checkout,
):
    # given
    transaction = TransactionItem.objects.create(
        name="Credit card",
        psp_reference=None,
        available_actions=["refund"],
        currency="USD",
        checkout_id=checkout.pk,
        charged_value=Decimal(10),
    )

    transaction_data = TransactionData(
        transaction=transaction,
        events=[],
    )

    # when
    result = generate_checkout_transactions_search_vector_value([transaction_data])

    # then
    # Should include only transaction global ID
    assert len(result) == 1


def test_generate_checkout_transactions_search_vector_value_with_multiple_events(
    checkout,
):
    # given
    transaction_psp_ref = "PSP-TRANS-123"
    event1_psp_ref = "EVENT-PSP-1"
    event2_psp_ref = "EVENT-PSP-2"

    transaction = TransactionItem.objects.create(
        name="Credit card",
        psp_reference=transaction_psp_ref,
        available_actions=["refund"],
        currency="USD",
        checkout_id=checkout.pk,
        charged_value=Decimal(10),
    )
    event1 = TransactionEvent.objects.create(
        psp_reference=event1_psp_ref,
        currency="USD",
        transaction=transaction,
        amount_value=Decimal(10),
    )
    event2 = TransactionEvent.objects.create(
        psp_reference=event2_psp_ref,
        currency="USD",
        transaction=transaction,
        amount_value=Decimal(10),
    )
    event3 = TransactionEvent.objects.create(
        psp_reference=None,
        currency="USD",
        transaction=transaction,
        amount_value=Decimal(10),
    )

    transaction_data = TransactionData(
        transaction=transaction,
        events=[event1, event2, event3],
    )

    # when
    result = generate_checkout_transactions_search_vector_value([transaction_data])

    # then
    assert len(result) == 4
    search_vector_values = _extract_search_vector_values(result)
    assert transaction_psp_ref in search_vector_values
    assert event1_psp_ref in search_vector_values
    assert event2_psp_ref in search_vector_values


def test_generate_checkout_transactions_search_vector_value_respects_max_limit(
    checkout, settings
):
    # given
    limit = 5
    settings.CHECKOUT_MAX_INDEXED_TRANSACTIONS = 5
    transactions_data = []
    for i in range(limit + 2):
        transaction = TransactionItem(
            name="Credit card",
            psp_reference=f"PSP-TRANS-{i}",
            available_actions=["refund"],
            currency="USD",
            checkout_id=checkout.pk,
            charged_value=Decimal(10),
        )
        transactions_data.append(
            TransactionData(
                transaction=transaction,
                events=[],
            )
        )

    # when
    result = generate_checkout_transactions_search_vector_value(transactions_data)

    # then
    # Should respect transaction limit (5) - 5 IDs + 5 psp_references = 10
    assert len(result) == limit * 2


def test_search_checkouts_with_value(checkout, checkout_JPY):
    # given
    checkout.email = "search@example.com"
    checkout.save(update_fields=["email"])
    update_checkouts_search_vector([checkout, checkout_JPY])
    qs = Checkout.objects.all()

    # when
    result = search_checkouts(qs, "search@example.com")

    # then
    assert result.count() == 1
    assert result.first() == checkout


def test_search_checkouts_without_value(checkout, checkout_JPY):
    # given
    qs = Checkout.objects.all()

    # when
    result = search_checkouts(qs, None)

    # then
    assert result.count() == Checkout.objects.count()


def test_search_checkouts_by_token(checkout, checkout_JPY):
    # given
    update_checkouts_search_vector([checkout, checkout_JPY])
    qs = Checkout.objects.all()

    # when
    result = search_checkouts(qs, str(checkout.token))

    # then
    assert result.count() == 1
    assert result.first() == checkout


def test_search_checkouts_by_user_email(checkout, checkout_JPY, customer_user):
    # given
    checkout.user = customer_user
    checkout.save(update_fields=["user"])

    checkout_JPY.user = customer_user
    checkout_JPY.save(update_fields=["user"])

    update_checkouts_search_vector([checkout, checkout_JPY])
    qs = Checkout.objects.all()

    # when
    result = search_checkouts(qs, customer_user.email)

    # then
    assert result.count() == 2


def test_search_checkouts_by_user_name(checkout, checkout_JPY, customer_user):
    # given
    checkout.user = customer_user
    checkout.save(update_fields=["user"])

    checkout_JPY.user = None
    checkout_JPY.save(update_fields=["user"])
    update_checkouts_search_vector([checkout, checkout_JPY])
    qs = Checkout.objects.all()

    # when
    result = search_checkouts(qs, customer_user.first_name)

    # then
    assert result.count() == 1
    assert result.first() == checkout


def test_search_checkouts_by_product_name(checkout_with_item, checkout_JPY, product):
    # given
    update_checkouts_search_vector([checkout_with_item, checkout_JPY])
    qs = Checkout.objects.all()

    # when
    result = search_checkouts(qs, product.name)

    # then
    assert result.count() == 1
    assert result.first() == checkout_with_item


def test_search_checkouts_by_sku(checkout_with_item, checkout_JPY):
    # given
    sku = "UNIQUE-SKU-999"
    line = checkout_with_item.lines.first()
    variant = line.variant
    variant.sku = sku
    variant.save(update_fields=["sku"])
    update_checkouts_search_vector([checkout_with_item, checkout_JPY])
    qs = Checkout.objects.all()

    # when
    result = search_checkouts(qs, sku)

    # then
    assert result.count() == 1
    assert result.first() == checkout_with_item


def test_search_checkouts_by_payment_psp_reference(checkout, checkout_JPY):
    # given
    psp_reference = "UNIQUE-PSP-REF-789"
    Payment.objects.create(
        gateway="mirumee.payments.dummy",
        is_active=True,
        checkout=checkout_JPY,
        total=Decimal("10.00"),
        currency="USD",
        psp_reference=psp_reference,
    )
    update_checkouts_search_vector([checkout, checkout_JPY])
    qs = Checkout.objects.all()

    # when
    result = search_checkouts(qs, psp_reference)

    # then
    assert result.count() == 1
    assert result.first() == checkout_JPY


def test_search_checkouts_by_transaction_psp_reference(checkout, checkout_JPY):
    # given
    psp_reference = "UNIQUE-TRANS-PSP-456"
    TransactionItem.objects.create(
        name="Credit card",
        psp_reference=psp_reference,
        available_actions=["refund"],
        currency="USD",
        checkout_id=checkout_JPY.pk,
        charged_value=Decimal(10),
    )
    update_checkouts_search_vector([checkout, checkout_JPY])
    qs = Checkout.objects.all()

    # when
    result = search_checkouts(qs, psp_reference)

    # then
    assert result.count() == 1
    assert result.first() == checkout_JPY


def test_search_checkouts_by_partial_email(checkout, checkout_with_item):
    # given
    checkout.email = "test@example.com"
    checkout.save(update_fields=["email"])
    checkout_with_item.email = "another@example.com"
    checkout_with_item.save(update_fields=["email"])

    update_checkouts_search_vector([checkout, checkout_with_item])
    qs = Checkout.objects.all()

    # when
    result = search_checkouts(qs, "test")

    # then
    results_list = list(result)
    assert len(results_list) == 1
    assert results_list[0] == checkout


def test_update_checkouts_search_vector_handles_deleted_checkout(
    checkout_with_item, checkout_JPY
):
    # given
    assert not checkout_with_item.search_vector
    assert not checkout_JPY.search_vector

    checkouts = [checkout_with_item, checkout_JPY]

    def delete_checkout(*args, **kwargs):
        Checkout.objects.filter(pk=checkout_JPY.pk).delete()

    # when
    with race_condition.RunAfter(
        "saleor.checkout.search.indexing.load_checkout_data", delete_checkout
    ):
        update_checkouts_search_vector(checkouts)

    # then
    checkout_with_item.refresh_from_db()
    assert checkout_with_item.search_vector
    assert checkout_with_item.search_index_dirty is False
    assert not Checkout.objects.filter(pk=checkout_JPY.pk).exists()


def test_update_checkouts_search_vector_handles_deleted_checkout_before_lock(
    checkout_with_item, checkout_JPY
):
    # given
    assert not checkout_with_item.search_vector
    assert not checkout_JPY.search_vector

    checkouts = [checkout_with_item, checkout_JPY]

    def delete_checkout(*args, **kwargs):
        Checkout.objects.filter(pk=checkout_JPY.pk).delete()

    # when
    with race_condition.RunBefore(
        "saleor.checkout.search.indexing.checkout_qs_select_for_update", delete_checkout
    ):
        update_checkouts_search_vector(checkouts)

    # then
    checkout_with_item.refresh_from_db()
    assert checkout_with_item.search_vector
    assert checkout_with_item.search_index_dirty is False
    assert not Checkout.objects.filter(pk=checkout_JPY.pk).exists()


def test_update_checkouts_search_vector_resets_flag_on_prepare_exception(
    checkout_with_item,
):
    # given
    checkout = checkout_with_item
    checkout.search_index_dirty = True
    checkout.save(update_fields=["search_index_dirty"])
    assert not checkout.search_vector

    # when
    with patch(
        "saleor.checkout.search.indexing.prepare_checkout_search_vector_value",
        side_effect=ValueError("Test error"),
    ):
        with pytest.raises(ValueError, match="Test error"):
            update_checkouts_search_vector([checkout])

    # then
    checkout.refresh_from_db()
    assert checkout.search_index_dirty is True
    assert not checkout.search_vector


def test_update_checkouts_search_vector_resets_flag_on_load_data_exception(
    checkout_with_item,
):
    # given
    checkout = checkout_with_item
    checkout.search_index_dirty = True
    checkout.save(update_fields=["search_index_dirty"])
    assert not checkout.search_vector

    # when
    with patch(
        "saleor.checkout.search.indexing.load_checkout_data",
        side_effect=RuntimeError("Database error"),
    ):
        with pytest.raises(RuntimeError, match="Database error"):
            update_checkouts_search_vector([checkout])

    # then
    checkout.refresh_from_db()
    assert checkout.search_index_dirty is True
    assert not checkout.search_vector
