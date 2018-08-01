import json

import graphene
import pytest
from django.shortcuts import reverse
from tests.utils import get_graphql_content

from saleor.page.models import Page


def test_page_query(user_api_client, page):
    page.is_visible = True
    query = """
    query PageQuery($id: ID!) {
        page(id: $id) {
            title
            slug
        }
    }
    """
    variables = json.dumps({
        'id': graphene.Node.to_global_id('Page', page.id)})
    response = user_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    page_data = content['data']['page']
    assert page_data['title'] == page.title
    assert page_data['slug'] == page.slug


def test_page_create_mutation(admin_api_client):
    query = """
        mutation CreatePage($slug: String!, $title: String!, $content: String!, $isVisible: Boolean!) {
            pageCreate(input: {slug: $slug, title: $title, content: $content, isVisible: $isVisible}) {
                page {
                    id
                    title
                    content
                    slug
                    isVisible
                }
                errors {
                    field
                    message
                }
            }
        }
    """
    page_slug = 'test-slug'
    page_content = 'test content'
    page_title = 'test title'
    page_isVisible = True

    # test creating root page
    variables = json.dumps({
        'title': page_title, 'content': page_content,
        'isVisible': page_isVisible, 'slug': page_slug})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['pageCreate']
    assert data['errors'] == []
    assert data['page']['title'] == page_title
    assert data['page']['content'] == page_content
    assert data['page']['slug'] == page_slug
    assert data['page']['isVisible'] == page_isVisible


def test_page_delete_mutation(admin_api_client, page):
    query = """
        mutation DeletePage($id: ID!) {
            pageDelete(id: $id) {
                page {
                    title
                    id
                }
                errors {
                    field
                    message
                }
              }
            }
    """
    variables = json.dumps({
        'id': graphene.Node.to_global_id('Page', page.id)})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['pageDelete']
    assert data['page']['title'] == page.title
    with pytest.raises(page._meta.model.DoesNotExist):
        page.refresh_from_db()


def test_paginate_pages(user_api_client, page):
    page.is_visible = True
    data_02 = {
        'slug': 'test02-url',
        'title': 'Test page',
        'content': 'test content',
        'is_visible': True}
    data_03 = {
        'slug': 'test03-url',
        'title': 'Test page',
        'content': 'test content',
        'is_visible': True}

    page2 = Page.objects.create(**data_02)
    page3 = Page.objects.create(**data_03)
    query = """
        query PagesQuery {
            pages(first: 2) {
                edges {
                    node {
                        id
                        title
                    }
                }
            }
        }
        """
    response = user_api_client.post(
        reverse('api'), {'query': query})
    content = get_graphql_content(response)
    assert 'errors' not in content
    pages_data = content['data']['pages']
    assert len(pages_data['edges']) == 2
