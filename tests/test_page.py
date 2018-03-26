import pytest


def test_draft_page_detail(client, admin_client, page):
    page_url = page.get_absolute_url()
    response = client.get(page_url)
    assert response.status_code == 404
    response = admin_client.get(page_url)
    assert response.status_code == 200


def test_public_page_detail(client, admin_client, page):
    page.is_visible = True
    page.save()
    page_url = page.get_absolute_url()
    response = client.get(page_url)
    assert response.status_code == 200
    response = admin_client.get(page_url)
    assert response.status_code == 200


@pytest.mark.parametrize(
    'title, seo_title, expected_result',
    (
        ('Title', 'Seo Title', 'Seo Title'),
        ('Title', None, 'Title')))
def test_page_get_seo_title(
        admin_client, page, title, seo_title, expected_result):
    page.title = title
    page.seo_title = seo_title
    page.save()
    result = page.get_seo_title()
    expected_result == result


@pytest.mark.parametrize(
    'seo_description, expected_result',
    (
        ('Seo', 'Seo'),
        (None, '')))
def test_page_get_seo_description(
        admin_client, page, seo_description, expected_result):
    page.seo_description = seo_description
    page.save()
    result = page.get_seo_description()
    expected_result == result
