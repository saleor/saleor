# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import postgresql_dashboard, postgresql_storefront


def search_storefront(phrase):
    return postgresql_storefront.search(phrase)


def search_dashboard(phrase):
    return postgresql_dashboard.search(phrase)
