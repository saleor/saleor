import uuid
from decimal import Decimal

import pytest

from ...models import TransactionItem
from ...transaction_item_calculations import recalculate_transaction_amounts
from ...utils import create_manual_adjustment_events


@pytest.fixture
def transaction_item_generator():
    def create_transaction(
        order_id=None,
        checkout_id=None,
        app=None,
        user=None,
        psp_reference="PSP ref1",
        name="Credit card",
        message="Transasction details",
        available_actions=None,
        authorized_value=Decimal(0),
        charged_value=Decimal(0),
        refunded_value=Decimal(0),
        canceled_value=Decimal(0),
        use_old_id=False,
        last_refund_success=True,
    ):
        if available_actions is None:
            available_actions = []
        transaction = TransactionItem.objects.create(
            token=uuid.uuid4(),
            name=name,
            message=message,
            psp_reference=psp_reference,
            available_actions=available_actions,
            currency="USD",
            order_id=order_id,
            checkout_id=checkout_id,
            app_identifier=app.identifier if app else None,
            app=app,
            user=user,
            use_old_id=use_old_id,
            last_refund_success=last_refund_success,
        )
        create_manual_adjustment_events(
            transaction=transaction,
            money_data={
                "authorized_value": authorized_value,
                "charged_value": charged_value,
                "refunded_value": refunded_value,
                "canceled_value": canceled_value,
            },
            user=user,
            app=app,
        )
        recalculate_transaction_amounts(transaction)
        return transaction

    return create_transaction


@pytest.fixture
def transaction_item_created_by_app(order, app, transaction_item_generator):
    charged_amount = Decimal("10.0")
    return transaction_item_generator(
        order_id=order.pk,
        checkout_id=None,
        app=app,
        user=None,
        charged_value=charged_amount,
    )


@pytest.fixture
def transaction_item_created_by_user(order, staff_user, transaction_item_generator):
    charged_amount = Decimal("10.0")
    return transaction_item_generator(
        order_id=order.pk,
        checkout_id=None,
        user=staff_user,
        app=None,
        charged_value=charged_amount,
    )


@pytest.fixture
def transaction_item(order, transaction_item_generator):
    return transaction_item_generator(
        order_id=order.pk,
    )
