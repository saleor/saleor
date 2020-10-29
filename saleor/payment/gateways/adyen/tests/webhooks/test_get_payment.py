import logging

import graphene
import pytest

from ...webhooks import get_payment

logger = logging.getLogger(__name__)


@pytest.mark.parametrize("payment_id", ["123", "Test payment ID"])
def test_get_payment_invalid_payment_id(payment_id, caplog):
    # given
    caplog.set_level(logging.WARNING)

    # when
    result = get_payment(payment_id)

    # then
    assert result is None
    assert f"Unable to decode the payment ID {payment_id}." in caplog.text


@pytest.mark.parametrize("payment_id", ["  ", None])
def test_get_payment_missing_payment_id(payment_id, caplog):
    # given
    caplog.set_level(logging.WARNING)

    # when
    result = get_payment(payment_id)

    # then
    assert result is None
    assert "Missing payment ID." in caplog.text


def test_get_payment_not_active_payment(payment_dummy, caplog):
    # given
    caplog.set_level(logging.WARNING)

    payment_dummy.is_active = False
    payment_dummy.save(update_fields=["is_active"])

    payment_id = graphene.Node.to_global_id("Payemnt", payment_dummy.pk)

    # when
    result = get_payment(payment_id)

    # then
    assert not result
    assert f"Payment for {payment_id} was not found." in caplog.text
