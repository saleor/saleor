"""
Belgium EID OpenId backend, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/belgium_eid.html
"""
from .open_id import OpenIdAuth


class BelgiumEIDOpenId(OpenIdAuth):
    """Belgium e-ID OpenID authentication backend"""
    name = 'belgiumeid'
    URL = 'https://www.e-contract.be/eid-idp/endpoints/openid/auth'
