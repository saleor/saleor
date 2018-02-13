from saleor.page.models import Page


def test_draft_page_detail(client, admin_client):
    url = '/page_draft'
    Page.objects.get_or_create(url=url, title='Draft', status=Page.DRAFT)
    response = client.get(url)
    assert response.status_code == 404
    response = admin_client.get(url)
    assert response.status_code == 200


def test_public_page_detail(client, admin_client):
    url = '/page'
    Page.objects.get_or_create(url=url, title='Public', status=Page.PUBLIC)
    response = client.get(url)
    assert response.status_code == 200
    response = admin_client.get(url)
    assert response.status_code == 200
