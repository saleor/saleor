from ..models import User
from ..utils import prepare_user_search_document_value, remove_staff_member


def test_remove_staff_member_with_orders(staff_user, permission_manage_products, order):
    # given
    order.user = staff_user
    order.save()
    staff_user.user_permissions.add(permission_manage_products)

    # when
    remove_staff_member(staff_user)

    # then
    staff_user = User.objects.get(pk=staff_user.pk)
    assert not staff_user.is_staff
    assert not staff_user.user_permissions.exists()


def test_remove_staff_member(staff_user):
    # when
    remove_staff_member(staff_user)

    # then
    assert not User.objects.filter(pk=staff_user.pk).exists()


def test_prepare_user_search_document_value(customer_user, address, address_usa):
    # given
    customer_user.addresses.set((address, address_usa))

    expected_search_value = (
        f"{customer_user.email}{customer_user.first_name}{customer_user.last_name}"
    )

    addresses = sorted([address, address_usa], key=lambda address: address.pk)

    for address in addresses:
        expected_search_value += (
            f"{address.first_name}{address.last_name}"
            f"{address.street_address_1}{address.street_address_2}"
            f"{address.city}{address.postal_code}{address.country}{address.phone}"
        )

    expected_search_value = expected_search_value.replace(" ", "").lower()

    # when
    search_document_value = prepare_user_search_document_value(customer_user)

    # then
    assert search_document_value == expected_search_value


def test_prepare_user_search_document_value_no_addresses(customer_user):
    # given
    customer_user.addresses.clear()

    expected_search_value = (
        f"{customer_user.email}{customer_user.first_name}{customer_user.last_name}"
    )

    # when
    search_document_value = prepare_user_search_document_value(customer_user)

    # then
    assert search_document_value == expected_search_value.lower()


def test_prepare_user_search_document_value_do_not_attach_addresses_data(
    customer_user, address, address_usa
):
    # given
    customer_user.addresses.set((address, address_usa))

    expected_search_value = (
        f"{customer_user.email}{customer_user.first_name}{customer_user.last_name}"
    )

    expected_search_value = expected_search_value.replace(" ", "").lower()

    # when
    search_document_value = prepare_user_search_document_value(
        customer_user, attach_addresses_data=False
    )

    # then
    assert search_document_value == expected_search_value
