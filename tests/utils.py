try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse


def get_redirect_location(response):
    # Due to Django 1.8 compatibility, we have to handle both cases
    location = response['Location']
    if location.startswith('http'):
        url = urlparse(location)
        location = url.path
    return location
