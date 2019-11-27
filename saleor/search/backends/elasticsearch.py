from . import elasticsearch_storefront


def search_storefront(phrase):
    return elasticsearch_storefront.search(phrase)
