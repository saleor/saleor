from . import postgresql_storefront


def search_storefront(phrase):
    return postgresql_storefront.search(phrase)
