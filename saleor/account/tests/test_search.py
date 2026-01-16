from ..search import update_user_search_vector


def test_update_user_search_vector(customer_user, address, address_usa):
    # given
    customer_user.addresses.set((address, address_usa))
    customer_user.search_vector = None

    # when
    update_user_search_vector(customer_user)

    # then
    customer_user.refresh_from_db()
    assert customer_user.search_vector is not None


def test_update_user_search_vector_no_addresses(customer_user):
    # given
    customer_user.addresses.clear()
    customer_user.search_vector = None

    # when
    update_user_search_vector(customer_user)

    # then
    customer_user.refresh_from_db()
    assert customer_user.search_vector is not None


def test_update_user_search_vector_without_save(customer_user, address, address_usa):
    # given
    customer_user.addresses.set((address, address_usa))
    initial_search_vector = customer_user.search_vector

    # when
    update_user_search_vector(customer_user, save=False)

    # then
    customer_user.refresh_from_db()
    # search_vector should be updated in memory but not saved to DB
    assert customer_user.search_vector == initial_search_vector
