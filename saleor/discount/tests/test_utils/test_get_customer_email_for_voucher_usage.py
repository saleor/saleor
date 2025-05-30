from ...utils.voucher import get_customer_email_for_voucher_usage


def test_get_customer_email_for_voucher_usage_for_checkout_info_without_user_data(
    checkout_info, customer_user
):
    # given
    checkout_info.user = None
    checkout_info.checkout.email = None
    checkout_info.checkout.user = None

    # when
    result = get_customer_email_for_voucher_usage(checkout_info)

    # then
    assert result is None


def test_get_customer_email_for_voucher_usage_for_checkout_info_with_user(
    checkout_info, customer_user
):
    # given
    checkout_info.user = customer_user
    checkout_info.checkout.save()

    # when
    result = get_customer_email_for_voucher_usage(checkout_info)

    # then
    assert result == checkout_info.user.email


def test_get_customer_email_for_voucher_usage_for_checkout_info_without_user(
    checkout_info,
):
    # given
    expected_email = "test@example.com"
    checkout_info.user = None
    checkout_info.checkout.email = expected_email

    # when
    result = get_customer_email_for_voucher_usage(checkout_info)

    # then
    assert result == expected_email


def test_get_customer_email_for_voucher_usage_for_checkout_with_user(
    checkout, customer_user
):
    # given
    checkout_email = "checkout@example.com"
    checkout.email = checkout_email
    checkout.user = customer_user
    checkout.save()

    # when
    result = get_customer_email_for_voucher_usage(checkout)

    # then
    assert result == customer_user.email


def test_get_customer_email_for_voucher_usage_for_checkout_without_user(checkout):
    # given
    expected_checkout_email = "checkout@example.com"
    checkout.user = None
    checkout.email = expected_checkout_email
    checkout.save()

    # when
    result = get_customer_email_for_voucher_usage(checkout)

    # then
    assert result == expected_checkout_email


def test_get_customer_email_for_voucher_usage_for_checkout_without_user_details(
    checkout,
):
    # given
    checkout.user = None
    checkout.email = None
    checkout.save()

    # when
    result = get_customer_email_for_voucher_usage(checkout)

    # then
    assert result is None


def test_get_customer_email_for_voucher_usage_for_order_with_user(order, customer_user):
    # given
    order_email = "order@example.com"
    order.user_email = order_email
    order.user = customer_user
    order.save()

    # when
    result = get_customer_email_for_voucher_usage(order)

    # then
    assert result == customer_user.email


def test_get_customer_email_for_voucher_usage_for_order_without_user(order):
    # given
    expected_order_email = "order@example.com"
    order.user = None
    order.user_email = expected_order_email
    order.save()

    # when
    result = get_customer_email_for_voucher_usage(order)

    # then
    assert result == expected_order_email


def test_get_customer_email_for_voucher_usage_for_order_without_user_details(order):
    # given
    order.user = None
    order.user_email = ""
    order.save()

    # when
    result = get_customer_email_for_voucher_usage(order)

    # then
    assert result is None
