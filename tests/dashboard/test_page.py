from unittest.mock import patch

import pytest
from django.conf import settings
from django.forms.models import model_to_dict
from django.urls import reverse

from saleor.dashboard.page.forms import PageForm
from saleor.page.models import Page


def test_page_list(admin_client):
    url = reverse('dashboard:page-list')

    response = admin_client.get(url)
    assert response.status_code == 200


def test_page_edit(admin_client, page):
    url = reverse('dashboard:page-update', args=[page.pk])
    assert not page.is_protected

    response = admin_client.get(url)
    assert response.status_code == 200
    data = {
        'slug': 'changed-url',
        'title': 'foo',
        'content': 'bar',
        'is_visible': True}

    response = admin_client.post(url, data=data)
    assert response.status_code == 302

    page.refresh_from_db()
    for attr, expected_value in data.items():
        assert getattr(page, attr) == expected_value


# sets the PROTECTED_PAGES setting, to contain the fixture default page slug
@patch.object(settings, 'PROTECTED_PAGES', ['test-url'])
def test_page_edit_protected_page(admin_client, page):
    """Tests if editing the slug from a protected page preserves the slug."""
    url = reverse('dashboard:page-update', args=[page.pk])
    assert page.is_protected

    response = admin_client.get(url)
    assert response.status_code == 200

    data = {
        'slug': 'changed-url',
        'title': 'foo',
        'content': 'bar',
        'is_visible': True}

    response = admin_client.post(url, data=data)
    assert response.status_code == 302

    page.refresh_from_db()
    assert page.slug == 'test-url'

    data.pop('slug')
    for attr, expected_value in data.items():
        assert getattr(page, attr) == expected_value


def test_page_add(admin_client):
    url = reverse('dashboard:page-add')

    response = admin_client.get(url)
    assert response.status_code == 200

    data = {
        'slug': 'aaaa',
        'title': 'foo',
        'content': 'bar',
        'is_visible': False}

    response = admin_client.post(url, data=data)
    assert response.status_code == 302

    page = Page.objects.last()

    for attr, expected_value in data.items():
        assert getattr(page, attr) == expected_value


def test_page_delete(admin_client, page):
    url = reverse('dashboard:page-delete', args=[page.pk])
    assert not page.is_protected

    response = admin_client.get(url)
    assert response.status_code == 200
    assert b'Are you sure you want to remove page' in response.content

    # send 'random' post data as in real usage it would be the CSRF token
    response = admin_client.post(url, data={'dummy': 'data'})
    assert response.status_code == 302

    with pytest.raises(page._meta.model.DoesNotExist):
        Page.objects.get(pk=page.pk)

    response = admin_client.get(url)
    assert response.status_code == 404


# sets the PROTECTED_PAGES setting, to contain the fixture default page slug
@patch.object(settings, 'PROTECTED_PAGES', ['test-url'])
def test_page_delete_protected(admin_client, page):
    """Tests if deleting a page having its slug protected page is denied."""
    url = reverse('dashboard:page-delete', args=[page.pk])
    expected_response_content = b'you cannot delete'
    assert page.is_protected

    response = admin_client.get(url)
    assert response.status_code == 200
    assert expected_response_content in response.content

    # send 'random' post data as in real usage it would be the CSRF token
    response = admin_client.post(url, data={'dummy': 'data'})
    assert response.status_code == 200
    assert expected_response_content in response.content

    # page should not have been deleted
    assert Page.objects.get(pk=page.pk)


def test_sanitize_page_content(page, default_category):
    data = model_to_dict(page)
    data['content'] = (
        '<b>bold</b><p><i>italic</i></p><h2>Header</h2><h3>subheader</h3>'
        '<blockquote>quote</blockquote>'
        '<p><a href="www.mirumee.com">link</a></p>'
        '<p>an <script>evil()</script>example</p>')
    form = PageForm(data, instance=page)
    assert form.is_valid()
    form.save()
    assert page.content == (
        '<b>bold</b><p><i>italic</i></p><h2>Header</h2><h3>subheader</h3>'
        '<blockquote>quote</blockquote>'
        '<p><a href="www.mirumee.com">link</a></p>'
        '<p>an &lt;script&gt;evil()&lt;/script&gt;example</p>')

    assert page.seo_description == (
        'bolditalicHeadersubheaderquotelinkan evil()example')


def test_set_page_seo_description(page):
    seo_description = (
        'This is a dummy page. '
        'HTML <b>shouldn\'t be removed</b> since it\'s a simple text field.')
    data = model_to_dict(page)
    data['price'] = 20
    data['content'] = 'a description'
    data['seo_description'] = seo_description

    form = PageForm(data, instance=page)

    assert form.is_valid()
    form.save()
    assert page.seo_description == seo_description
