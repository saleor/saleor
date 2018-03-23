from django.urls import reverse

from saleor.dashboard.page.forms import PageForm
from django.forms.models import model_to_dict


def test_page_list(admin_client):
    url = reverse('dashboard:page-list')

    response = admin_client.get(url)
    assert response.status_code == 200


def test_page_edit(admin_client, page):
    url = reverse('dashboard:page-update', args=[page.pk])

    response = admin_client.get(url)
    assert response.status_code == 200
    data = {
        'slug': 'changed-url',
        'title': 'foo',
        'content': 'bar',
        'visible': True}

    response = admin_client.post(url, data=data)
    assert response.status_code == 302


def test_page_add(admin_client):
    url = reverse('dashboard:page-add')

    response = admin_client.get(url)
    assert response.status_code == 200

    data = {
        'slug': 'aaaa',
        'title': 'foo',
        'content': 'bar',
        'visible': False}

    response = admin_client.post(url, data=data)
    assert response.status_code == 302


def test_page_delete(admin_client, page):
    url = reverse('dashboard:page-delete', args=[page.pk])

    response = admin_client.get(url)
    assert response.status_code == 200

    response = admin_client.post(url, data={'a': 'b'})
    assert response.status_code == 302


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
