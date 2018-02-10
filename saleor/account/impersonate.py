# Module used to config django-impersonate app
from .models import User


def get_impersonatable_users(request):
    """Return all users that can be impersonated."""
    return User.objects.filter(is_staff=False, is_superuser=False)


def can_impersonate(request):
    """Check if the current user can impersonate customers.

    `django-impersonate` module requires a function as input argument,
    not just permission name.
    """
    return request.user.has_perm('account.impersonate_user')
