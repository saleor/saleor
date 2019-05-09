"""
LiveJournal OpenId backend, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/livejournal.html
"""
from six.moves.urllib_parse import urlsplit

from .open_id import OpenIdAuth
from ..exceptions import AuthMissingParameter


class LiveJournalOpenId(OpenIdAuth):
    """LiveJournal OpenID authentication backend"""
    name = 'livejournal'

    def get_user_details(self, response):
        """Generate username from identity url"""
        values = super(LiveJournalOpenId, self).get_user_details(response)
        values['username'] = values.get('username') or \
                             urlsplit(response.identity_url)\
                                .netloc.split('.', 1)[0]
        return values

    def openid_url(self):
        """Returns LiveJournal authentication URL"""
        if not self.data.get('openid_lj_user'):
            raise AuthMissingParameter(self, 'openid_lj_user')
        return 'http://{0}.livejournal.com'.format(self.data['openid_lj_user'])
