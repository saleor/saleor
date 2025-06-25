from .models import User


def user_qs_select_for_update():
    return User.objects.order_by("pk").select_for_update(of=("self",))
