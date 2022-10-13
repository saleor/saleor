from ..search import prepare_user_search_document_value


def test_prepare_user_search_document_value(customer_user, address, address_usa):
    # given
    customer_user.addresses.set((address, address_usa))

    expected_search_value = (
        f"{customer_user.email}\n{customer_user.first_name}"
        f"\n{customer_user.last_name}\n"
    )

    addresses = sorted([address, address_usa], key=lambda address: address.pk)

    for address in addresses:
        expected_search_value += (
            f"{address.first_name}\n{address.last_name}\n"
            f"{address.street_address_1}\n{address.street_address_2}\n"
            f"{address.city}\n{address.postal_code}\n{address.country.name}\n"
            f"{address.country.code}\n{address.phone}\n"
        )

    expected_search_value = expected_search_value.lower()

    # when
    search_document_value = prepare_user_search_document_value(customer_user)

    # then
    assert search_document_value == expected_search_value


def test_prepare_user_search_document_value_no_addresses(customer_user):
    # given
    customer_user.addresses.clear()

    expected_search_value = (
        f"{customer_user.email}\n{customer_user.first_name}"
        f"\n{customer_user.last_name}\n"
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
        f"{customer_user.email}\n{customer_user.first_name}"
        f"\n{customer_user.last_name}\n"
    ).lower()

    # when
    search_document_value = prepare_user_search_document_value(
        customer_user, attach_addresses_data=False
    )

    # then
    assert search_document_value == expected_search_value
