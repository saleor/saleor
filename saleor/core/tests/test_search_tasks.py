from ...account.search import update_user_search_vector
from ...core.postgres import FlatConcatSearchVector
from ...core.search_tasks import (
    set_order_search_document_values,
    set_user_search_document_values,
)


def test_set_user_search_document_values(customer_user, customer_user2):
    # given
    assert not customer_user.search_vector

    update_user_search_vector(customer_user2)
    customer_user2.refresh_from_db()
    assert customer_user2.search_vector
    search_vector_customer_2 = customer_user2.search_vector

    # when
    set_user_search_document_values()

    # then
    customer_user.refresh_from_db()
    customer_user2.refresh_from_db()
    assert customer_user.search_vector
    assert customer_user.email in customer_user.search_vector
    assert customer_user2.search_vector == search_vector_customer_2


def test_set_order_search_document_values_already_present(
    order_generator,
):
    # given
    order = order_generator(search_vector_class=FlatConcatSearchVector)
    order.refresh_from_db()
    vector = order.search_vector

    # when
    set_order_search_document_values()

    # then
    order.refresh_from_db()
    assert order.search_vector == vector


def test_set_order_search_document_values_no_vector(order):
    # given
    order.refresh_from_db()
    assert order.search_vector is None

    # when
    set_order_search_document_values()

    # then
    order.refresh_from_db()
    assert order.user.email in order.search_vector
