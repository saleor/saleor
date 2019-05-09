"""
AOL OpenId backend, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/aol.html
"""
from .open_id import OpenIdAuth


class AOLOpenId(OpenIdAuth):
    name = 'aol'
    URL = 'http://openid.aol.com'
