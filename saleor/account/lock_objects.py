from .models import CustomerType, User


def user_qs_select_for_update():
    return User.objects.order_by("pk").select_for_update(of=("self",))


def customer_type_qs_select_for_update():
    return CustomerType.objects.order_by("pk").select_for_update(of=("self",))
