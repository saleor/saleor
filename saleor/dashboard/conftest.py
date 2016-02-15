import pytest

@pytest.fixture()
def admin_user(db, django_user_model, django_username_field):
    """A Django admin user.

    This uses an existing user with username "admin", or creates a new one with
    password "password".
    """
    UserModel = django_user_model
    username_field = django_username_field

    try:
        user = UserModel._default_manager.get(**{username_field: 'admin'})
    except UserModel.DoesNotExist:
        extra_fields = {}
        if username_field not in {'username', 'email'}:
            extra_fields[username_field] = 'admin'
        user = UserModel._default_manager.create_superuser(
            'admin@example.com', 'password', **extra_fields)
    return user


@pytest.fixture()
def admin_client(db, admin_user):
    """A Django test client logged in as an admin user."""
    from django.test.client import Client

    client = Client()
    client.login(username=admin_user.email, password='password')
    return client
