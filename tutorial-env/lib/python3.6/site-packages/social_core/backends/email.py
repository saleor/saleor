"""
Legacy Email backend, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/email.html
"""
from .legacy import LegacyAuth


class EmailAuth(LegacyAuth):
    name = 'email'
    ID_KEY = 'email'
    REQUIRES_EMAIL_VALIDATION = True
    EXTRA_DATA = ['email']
