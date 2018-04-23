def test_draft_page_details(client, admin_client, page):
    page_url = page.get_absolute_url()
    response = client.get(page_url)
    assert response.status_code == 404
    response = admin_client.get(page_url)
    assert response.status_code == 200


def test_public_page_details(client, admin_client, page):
    page.is_visible = True
    page.save()
    page_url = page.get_absolute_url()
    response = client.get(page_url)
    assert response.status_code == 200
    response = admin_client.get(page_url)
    assert response.status_code == 200
