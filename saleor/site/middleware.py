from .utils import get_site_settings


class SiteSettingMiddleware(object):
    def process_request(self, request):
        get_site_settings(request)
