import json

import graphene
import pytest
from django.utils.text import slugify

from saleor.page.models import Page
from tests.api.utils import get_graphql_content

PAGE_QUERY = """
    query PageQuery($id: ID, $slug: String) {
        page(id: $id, slug: $slug) {
            title
            slug
        }
    }
"""


def test_query_published_page(user_api_client, page):
    page.is_published = True
    page.save()

    # query by ID
    variables = {'id': graphene.Node.to_global_id('Page', page.id)}
    response = user_api_client.post_graphql(PAGE_QUERY, variables)
    content = get_graphql_content(response)
    page_data = content['data']['page']
    assert page_data['title'] == page.title
    assert page_data['slug'] == page.slug

    # query by slug
    variables = {'slug': page.slug}
    response = user_api_client.post_graphql(PAGE_QUERY, variables)
    content = get_graphql_content(response)
    assert content['data']['page'] is not None


def test_customer_query_unpublished_page(user_api_client, page):
    page.is_published = False
    page.save()

    # query by ID
    variables = {'id': graphene.Node.to_global_id('Page', page.id)}
    response = user_api_client.post_graphql(PAGE_QUERY, variables)
    content = get_graphql_content(response)
    assert content['data']['page'] is None

    # query by slug
    variables = {'slug': page.slug}
    response = user_api_client.post_graphql(PAGE_QUERY, variables)
    content = get_graphql_content(response)
    assert content['data']['page'] is None


def test_staff_query_unpublished_page(
        staff_api_client, page, permission_manage_pages):
    page.is_published = False
    page.save()

    # query by ID
    variables = {'id': graphene.Node.to_global_id('Page', page.id)}
    response = staff_api_client.post_graphql(PAGE_QUERY, variables)
    content = get_graphql_content(response)
    assert content['data']['page'] is None
    # query by slug
    variables = {'slug': page.slug}
    response = staff_api_client.post_graphql(PAGE_QUERY, variables)
    content = get_graphql_content(response)
    assert content['data']['page'] is None

    # query by ID with page permissions
    variables = {'id': graphene.Node.to_global_id('Page', page.id)}
    response = staff_api_client.post_graphql(
        PAGE_QUERY,
        variables,
        permissions=[permission_manage_pages],
        check_no_permissions=False)
    content = get_graphql_content(response)
    assert content['data']['page'] is not None
    # query by slug with page permissions
    variables = {'slug': page.slug}
    response = staff_api_client.post_graphql(
        PAGE_QUERY,
        variables,
        permissions=[permission_manage_pages],
        check_no_permissions=False)
    content = get_graphql_content(response)
    assert content['data']['page'] is not None


CREATE_PAGE_MUTATION = """
    mutation CreatePage(
            $slug: String, $title: String, $content: String,
            $contentJson: JSONString, $isPublished: Boolean) {
        pageCreate(
                input: {
                    slug: $slug, title: $title,
                    content: $content, contentJson: $contentJson
                    isPublished: $isPublished}) {
            page {
                id
                title
                content
                contentJson
                slug
                isPublished
            }
            errors {
                field
                message
            }
        }
    }
"""


def test_page_create_mutation(staff_api_client, permission_manage_pages):
    page_slug = 'test-slug'
    page_content = 'test content'
    page_content_json = json.dumps({'content': 'test content'})
    page_title = 'test title'
    page_is_published = True

    # test creating root page
    variables = {
        'title': page_title,
        'content': page_content,
        'contentJson': page_content_json,
        'isPublished': page_is_published,
        'slug': page_slug}
    response = staff_api_client.post_graphql(
        CREATE_PAGE_MUTATION, variables, permissions=[permission_manage_pages])
    content = get_graphql_content(response)
    data = content['data']['pageCreate']
    assert data['errors'] == []
    assert data['page']['title'] == page_title
    assert data['page']['content'] == page_content
    assert data['page']['contentJson'] == page_content_json
    assert data['page']['slug'] == page_slug
    assert data['page']['isPublished'] == page_is_published


def test_create_default_slug(staff_api_client, permission_manage_pages):
    # test creating root page
    title = 'Spanish inquisition'
    response = staff_api_client.post_graphql(
        CREATE_PAGE_MUTATION, {'title': title},
        permissions=[permission_manage_pages])
    content = get_graphql_content(response)
    data = content['data']['pageCreate']
    assert not data['errors']
    assert data['page']['title'] == title
    assert data['page']['slug'] == slugify(title)


def test_page_delete_mutation(staff_api_client, page, permission_manage_pages):
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
    variables = {'id': graphene.Node.to_global_id('Page', page.id)}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_pages])
    content = get_graphql_content(response)
    data = content['data']['pageDelete']
    assert data['page']['title'] == page.title
    with pytest.raises(page._meta.model.DoesNotExist):
        page.refresh_from_db()


def test_paginate_pages(user_api_client, page):
    page.is_published = True
    data_02 = {
        'slug': 'test02-url',
        'title': 'Test page',
        'content': 'test content',
        'is_published': True}
    data_03 = {
        'slug': 'test03-url',
        'title': 'Test page',
        'content': 'test content',
        'is_published': True}

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
    response = user_api_client.post_graphql(query)
    content = get_graphql_content(response)
    pages_data = content['data']['pages']
    assert len(pages_data['edges']) == 2


MUTATION_PUBLISH_PAGES = """
    mutation publishManyPages($ids: [ID]!, $is_published: Boolean!) {
        pageBulkPublish(ids: $ids, isPublished: $is_published) {
            count
        }
    }
    """


def test_bulk_publish(
        staff_api_client, page_list_unpublished,
        permission_manage_pages):
    page_list = page_list_unpublished
    assert not any(page.is_published for page in page_list)


    variables = {'ids': [
        graphene.Node.to_global_id('Page', page.id)
        for page in page_list], 'is_published': True}
    response = staff_api_client.post_graphql(
        MUTATION_PUBLISH_PAGES, variables, permissions=[permission_manage_pages])
    content = get_graphql_content(response)
    page_list = Page.objects.filter(id__in=[page.pk for page in page_list])

    assert content['data']['pageBulkPublish']['count'] == len(page_list)
    assert all(page.is_published for page in page_list)


def test_bulk_unpublish(
        staff_api_client, page_list,
        permission_manage_pages):
    assert all(page.is_published for page in page_list)
    variables = {'ids': [
        graphene.Node.to_global_id('Page', page.id)
        for page in page_list], 'is_published': False}
    response = staff_api_client.post_graphql(
        MUTATION_PUBLISH_PAGES, variables, permissions=[permission_manage_pages])
    content = get_graphql_content(response)
    page_list = Page.objects.filter(id__in=[page.pk for page in page_list])

    assert content['data']['pageBulkPublish']['count'] == len(page_list)
    assert not any(page.is_published for page in page_list)
