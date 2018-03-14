import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse

from saleor.account.backends import BaseBackend
from saleor.account.forms import LoginForm, SignupForm

from .utils import get_redirect_location

User = get_user_model()


@pytest.fixture
def base_backend():
    base_backend = BaseBackend()
    base_backend.DB_NAME = 'Backend'
    return base_backend


def test_login_form_valid(customer_user):
    data = {'username': 'test@example.com', 'password': 'password'}
    form = LoginForm(data=data)
    assert form.is_valid()
    assert form.get_user() == customer_user


def test_login_form_not_valid(customer_user):
    data = {'user': 'test@example.com', 'password': 'wrongpassword'}
    form = LoginForm(data=data)
    assert not form.is_valid()
    assert form.get_user_id() is None


def test_login_view_valid(client, customer_user):
    url = reverse('account:login')
    response = client.post(
        url, {'username': 'test@example.com', 'password': 'password'},
        follow=True)
    assert response.context['user'] == customer_user


def test_login_view_not_valid(client, customer_user):
    url = reverse('account:login')
    response = client.post(
        url, {'username': 'test@example.com', 'password': 'wrong'},
        follow=True)
    assert isinstance(response.context['user'], AnonymousUser)


def test_login_view_next(client, customer_user):
    url = reverse('account:login') + '?next=/cart/'
    post_data = {'username': 'test@example.com', 'password': 'password'}
    response = client.post(url, post_data, follow=True)
    redirect_location = response.request['PATH_INFO']
    assert redirect_location == reverse('cart:index')


def test_login_view_redirect(client, customer_user):
    url = reverse('account:login')
    data = {
        'username': 'test@example.com', 'password': 'password',
        'next': reverse('cart:index')}
    response = client.post(url, data, follow=True)
    redirect_location = response.request['PATH_INFO']
    assert redirect_location == reverse('cart:index')


def test_logout_view_no_user(client):
    url = reverse('account:logout')
    response = client.get(url, follow=True)
    redirect_location = response.request['PATH_INFO']
    assert reverse('account:login') == redirect_location


def test_logout_with_user(authorized_client):
    url = reverse('account:logout')
    response = authorized_client.get(url, follow=True)
    assert isinstance(response.context['user'], AnonymousUser)


def test_signup_form_empty():
    form = SignupForm({})
    assert not form.is_valid()


def test_signup_form_not_valid():
    data = {'email': 'admin@example', 'password': 'password'}
    form = SignupForm(data)
    assert not form.is_valid()
    assert 'email' in form.errors


def test_signup_form_user_exists(customer_user):
    data = {'email': customer_user.email, 'password': 'password'}
    form = SignupForm(data)
    assert not form.is_valid()
    assert form.errors['email']


def test_signup_view_create_user(client, db):
    url = reverse('account:signup')
    data = {'email': 'client@example.com', 'password': 'password'}
    response = client.post(url, data)
    assert User.objects.count() == 1
    assert User.objects.filter(email='client@example.com').exists()
    redirect_location = get_redirect_location(response)
    assert redirect_location == reverse('home')


def test_signup_view_redirect(client, customer_user):
    url = reverse('account:signup')
    data = {
        'email': 'client@example.com', 'password': 'password',
        'next': reverse('cart:index')}
    response = client.post(url, data)
    redirect_location = get_redirect_location(response)
    assert redirect_location == reverse('cart:index')


def test_signup_view_fail(client, db, customer_user):
    url = reverse('account:signup')
    data = {'email': customer_user.email, 'password': 'password'}
    client.post(url, data)
    assert User.objects.count() == 1


def test_password_reset_view_post(client, db):
    url = reverse('account:reset-password')
    data = {'email': 'test@examle.com'}
    response = client.post(url, data)
    redirect_location = get_redirect_location(response)
    assert redirect_location == reverse('account:reset-password-done')


def test_password_reset_view_get(client, db):
    url = reverse('account:reset-password')
    response = client.get(url)
    assert response.status_code == 200
    assert response.template_name == ['account/password_reset.html']


def test_base_backend(authorization_key, base_backend):
    assert authorization_key.site_settings.site.domain == 'mirumee.com'
    key, secret = base_backend.get_key_and_secret()
    assert key == 'Key'
    assert secret == 'Password'


def test_backend_no_site(settings, authorization_key, base_backend):
    settings.SITE_ID = None
    assert base_backend.get_key_and_secret() is None
