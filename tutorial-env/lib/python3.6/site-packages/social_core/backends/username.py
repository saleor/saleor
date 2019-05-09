"""
Legacy Username backend, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/username.html
"""
from .legacy import LegacyAuth


class UsernameAuth(LegacyAuth):
    name = 'username'
    ID_KEY = 'username'
    EXTRA_DATA = ['username']
