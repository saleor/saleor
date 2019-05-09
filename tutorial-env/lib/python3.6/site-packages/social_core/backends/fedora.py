"""
Fedora OpenId backend, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/fedora.html
"""
from .open_id import OpenIdAuth


class FedoraOpenId(OpenIdAuth):
    name = 'fedora'
    URL = 'https://id.fedoraproject.org'
    USERNAME_KEY = 'nickname'
