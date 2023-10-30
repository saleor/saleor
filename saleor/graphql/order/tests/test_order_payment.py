import graphene
import pytest
from django.core.exceptions import ValidationError

from ....order import events as order_events
from ....order.models import OrderEvent
from ....payment import PaymentError
from ...tests.utils import get_graphql_content
from ..mutations.utils import try_payment_action


@pytest.mark.parametrize(
    ("requires_amount", "mutation_name"),
    [(True, "orderRefund"), (False, "orderVoid"), (True, "orderCapture")],
)
def test_clean_payment_without_payment_associated_to_order(
    staff_api_client,
    permission_group_manage_orders,
    order,
    requires_amount,
    mutation_name,
):
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    assert not OrderEvent.objects.exists()

    additional_arguments = ", amount: 2" if requires_amount else ""
    query = f"""
        mutation {mutation_name}($id: ID!) {{
          {mutation_name}(id: $id {additional_arguments}) {{
            errors {{
              field
              message
            }}
          }}
        }}
    """

    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(query, variables)
    errors = get_graphql_content(response)["data"][mutation_name].get("errors")

    message = "There's no payment associated with the order."

    assert errors, "expected an error"
    assert errors == [{"field": "payment", "message": message}]
    assert not OrderEvent.objects.exists()


def test_try_payment_action_generates_event(order, staff_user, payment_dummy):
    message = "The payment did a oopsie!"
    assert not OrderEvent.objects.exists()

    def _test_operation():
        raise PaymentError(message)

    with pytest.raises(ValidationError) as exc:
        try_payment_action(
            order=order,
            user=staff_user,
            app=None,
            payment=payment_dummy,
            func=_test_operation,
        )

    assert exc.value.args[0]["payment"].message == message

    error_event = OrderEvent.objects.get()  # type: OrderEvent
    assert error_event.type == order_events.OrderEvents.PAYMENT_FAILED
    assert error_event.user == staff_user
    assert not error_event.app
    assert error_event.parameters == {
        "message": message,
        "gateway": payment_dummy.gateway,
        "payment_id": payment_dummy.token,
    }


def test_try_payment_action_generates_app_event(order, app, payment_dummy):
    message = "The payment did a oopsie!"
    assert not OrderEvent.objects.exists()

    def _test_operation():
        raise PaymentError(message)

    with pytest.raises(ValidationError) as exc:
        try_payment_action(
            order=order, user=None, app=app, payment=payment_dummy, func=_test_operation
        )

    assert exc.value.args[0]["payment"].message == message

    error_event = OrderEvent.objects.get()  # type: OrderEvent
    assert error_event.type == order_events.OrderEvents.PAYMENT_FAILED
    assert not error_event.user
    assert error_event.app == app
    assert error_event.parameters == {
        "message": message,
        "gateway": payment_dummy.gateway,
        "payment_id": payment_dummy.token,
    }
