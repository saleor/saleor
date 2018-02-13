from django.urls import reverse

from ..page.models import Page


def test_page_list(admin_client):
    url = reverse('dashboard:page-list')

    response = admin_client.get(url)
    assert response.status_code == 200


def test_page_edit(admin_client):
    page = Page.objects.create(url='aaaa', title='foo', content='bar')
    url = reverse('dashboard:page-edit', args=[page.pk])

    response = admin_client.get(url)
    assert response.status_code == 200
    data = {
        'url': 'aaaa',
        'title': 'foo',
        'content': 'bar',
        'status': Page.PUBLIC,
        'assets-TOTAL_FORMS': 0,
        'assets-INITIAL_FORMS': 0}

    response = admin_client.post(url, data=data)
    assert response.status_code == 302


def test_page_add(admin_client):
    url = reverse('dashboard:page-add')

    response = admin_client.get(url)
    assert response.status_code == 200

    data = {
        'url': 'aaaa',
        'title': 'foo',
        'content': 'bar',
        'status': Page.DRAFT,
        'assets-TOTAL_FORMS': 0,
        'assets-INITIAL_FORMS': 0}

    response = admin_client.post(url, data=data)
    assert response.status_code == 302


def test_page_delete(admin_client):
    page = Page.objects.create(url='aaaa', title='foo', content='bar')
    url = reverse('dashboard:page-delete', args=[page.pk])

    response = admin_client.get(url)
    assert response.status_code == 200

    response = admin_client.post(url, data={'a': 'b'})
    assert response.status_code == 302
