import json

from ..utils import update_payment_with_action_required_data


def test_update_payment_with_action_required_data_empty_extra_data(
    payment_adyen_for_checkout,
):
    # given
    payment_adyen_for_checkout.extra_data = ""
    payment_adyen_for_checkout.save(update_fields=["extra_data"])

    action = {
        "paymentData": "test_data",
    }
    details = [
        {"key": "payload", "type": "text"},
        {"key": "secondParam", "type": "text"},
    ]

    # when
    update_payment_with_action_required_data(
        payment_adyen_for_checkout, action, details
    )

    # then
    payment_adyen_for_checkout.refresh_from_db()
    extra_data = json.loads(payment_adyen_for_checkout.extra_data)
    assert len(extra_data) == 1
    assert extra_data[0]["payment_data"] == action["paymentData"]
    assert set(extra_data[0]["parameters"]) == {"payload", "secondParam"}


def test_update_payment_with_action_required_data_extra_data_as_list(
    payment_adyen_for_checkout,
):
    # given
    payment_adyen_for_checkout.extra_data = json.dumps([{"test_data": "test"}])
    payment_adyen_for_checkout.save(update_fields=["extra_data"])

    action = {
        "paymentData": "test_data",
    }
    details = [
        {"key": "payload", "type": "text"},
        {"key": "secondParam", "type": "text"},
    ]

    # when
    update_payment_with_action_required_data(
        payment_adyen_for_checkout, action, details
    )

    # then
    payment_adyen_for_checkout.refresh_from_db()
    extra_data = json.loads(payment_adyen_for_checkout.extra_data)
    assert len(extra_data) == 2
    assert extra_data[1]["payment_data"] == action["paymentData"]
    assert set(extra_data[1]["parameters"]) == {"payload", "secondParam"}


def test_update_payment_with_action_required_data_extra_data_as_dict(
    payment_adyen_for_checkout,
):
    # given
    payment_adyen_for_checkout.extra_data = json.dumps({"test_data": "test"})
    payment_adyen_for_checkout.save(update_fields=["extra_data"])

    action = {
        "paymentData": "test_data",
    }
    details = [
        {"key": "payload", "type": "text"},
        {"key": "secondParam", "type": "text"},
    ]

    # when
    update_payment_with_action_required_data(
        payment_adyen_for_checkout, action, details
    )

    # then
    payment_adyen_for_checkout.refresh_from_db()
    extra_data = json.loads(payment_adyen_for_checkout.extra_data)
    assert len(extra_data) == 2
    assert extra_data[1]["payment_data"] == action["paymentData"]
    assert set(extra_data[1]["parameters"]) == {"payload", "secondParam"}
