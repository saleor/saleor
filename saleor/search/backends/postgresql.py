from . import postgresql_dashboard, postgresql_storefront


def search_storefront(phrase):
    return postgresql_storefront.search(phrase)


def search_dashboard(phrase):
    return postgresql_dashboard.search(phrase)
