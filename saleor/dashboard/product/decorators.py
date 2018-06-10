from django.http.response import HttpResponseRedirectBase
from ...product.utils.json_cache_manager import refresh_json_product_list_cache


def refresh_product_list_on_redirect(view):
    def process(*args, **kwargs):
        response = view(*args, **kwargs)
        if isinstance(response, HttpResponseRedirectBase):
            refresh_json_product_list_cache.delay()
        return response
    return process
