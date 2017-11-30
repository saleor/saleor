# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import elasticsearch_dashboard, elasticsearch_storefront


def search_storefront(phrase):
    return elasticsearch_storefront.search(phrase)


def search_dashboard(phrase):
    return elasticsearch_dashboard.search(phrase)
