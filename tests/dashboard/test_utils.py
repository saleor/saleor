from django.test.client import RequestFactory
from django.urls import reverse

from saleor.dashboard.templatetags.utils import construct_get_query, paginate


def test_construct_get_query_get_and_params():
    request = RequestFactory().get(reverse('dashboard:product-list'))
    context = {'request': request}
    result = construct_get_query(context, param1='param1', param2='param2',
                                 page='3')
    assert result.startswith('?')
    result = result[1:].split('&')
    assert 'param1=param1' in result
    assert 'param2=param2' in result
    assert 'page=3' in result


def test_construct_get_query_params():
    request = RequestFactory().get(reverse('dashboard:product-list'))
    context = {'request': request}
    result = construct_get_query(context)
    assert result == ''


def test_paginate():
    request = RequestFactory().get(reverse('dashboard:product-list'))
    context = {'request': request}
    result = paginate(context, 'page_obj')
    assert result['n_forward'] == 6
    assert result['n_backward'] == -6
    assert result['next_section'] == 11
    assert result['previous_section'] == -11
