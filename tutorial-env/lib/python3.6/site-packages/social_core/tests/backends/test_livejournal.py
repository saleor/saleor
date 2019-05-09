import datetime

from httpretty import HTTPretty

from six.moves.urllib_parse import urlencode

from ...exceptions import AuthMissingParameter

from .open_id import OpenIdTest


JANRAIN_NONCE = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')


class LiveJournalOpenIdTest(OpenIdTest):
    backend_path = 'social_core.backends.livejournal.LiveJournalOpenId'
    expected_username = 'foobar'
    discovery_body = ''.join([
      '<xrds:XRDS xmlns:xrds="xri://$xrds" xmlns="xri://$xrd*($v*2.0)">',
      '<XRD>',
      '<Service priority="0">',
      '<Type>http://specs.openid.net/auth/2.0/signon</Type>',
      '<URI>http://www.livejournal.com/openid/server.bml</URI>',
      '<LocalID>http://foobar.livejournal.com/</LocalID>',
      '</Service>',
      '</XRD>',
      '</xrds:XRDS>'
    ])
    server_response = urlencode({
        'janrain_nonce': JANRAIN_NONCE,
        'openid.mode': 'id_res',
        'openid.claimed_id': 'http://foobar.livejournal.com/',
        'openid.identity': 'http://foobar.livejournal.com/',
        'openid.op_endpoint': 'http://www.livejournal.com/openid/server.bml',
        'openid.return_to': 'http://myapp.com/complete/livejournal/?'
                            'janrain_nonce=' + JANRAIN_NONCE,
        'openid.response_nonce': JANRAIN_NONCE + 'wGp2rj',
        'openid.assoc_handle': '1364932966:ZTiur8sem3r2jzZougMZ:4d1cc3b44e',
        'openid.ns': 'http://specs.openid.net/auth/2.0',
        'openid.signed': 'mode,claimed_id,identity,op_endpoint,return_to,'
                         'response_nonce,assoc_handle',
        'openid.sig': 'Z8MOozVPTOBhHG5ZS1NeGofxs1Q=',
    })
    server_bml_body = '\n'.join([
        'assoc_handle:1364935340:ZhruPQ7DJ9eGgUkeUA9A:27f8c32464',
        'assoc_type:HMAC-SHA1',
        'dh_server_public:WzsRyLomvAV3vwvGUrfzXDgfqnTF+m1l3JWb55fyHO7visPT4tmQ'
        'iTjqFFnSVAtAOvQzoViMiZQisxNwnqSK4lYexoez1z6pP5ry3pqxJAEYj60vFGvRztict'
        'Eo0brjhmO1SNfjK1ppjOymdykqLpZeaL5fsuLtMCwTnR/JQZVA=',
        'enc_mac_key:LiOEVlLJSVUqfNvb5zPd76nEfvc=',
        'expires_in:1207060',
        'ns:http://specs.openid.net/auth/2.0',
        'session_type:DH-SHA1',
        ''
    ])

    def openid_url(self):
        return super(LiveJournalOpenIdTest, self).openid_url() + '/data/yadis'

    def post_start(self):
        self.strategy.remove_from_request_data('openid_lj_user')

    def _setup_handlers(self):
        HTTPretty.register_uri(
            HTTPretty.POST,
            'http://www.livejournal.com/openid/server.bml',
            headers={'Accept-Encoding': 'identity',
                     'Content-Type': 'application/x-www-form-urlencoded'},
            status=200,
            body=self.server_bml_body
        )
        HTTPretty.register_uri(
            HTTPretty.GET,
            'http://foobar.livejournal.com/',
            headers={
                'Accept-Encoding': 'identity',
                'Accept': 'text/html; q=0.3,'
                          'application/xhtml+xml; q=0.5,'
                          'application/xrds+xml'
            },
            status=200,
            body=self.discovery_body
        )

    def test_login(self):
        self.strategy.set_request_data({'openid_lj_user': 'foobar'},
                                       self.backend)
        self._setup_handlers()
        self.do_login()

    def test_partial_pipeline(self):
        self.strategy.set_request_data({'openid_lj_user': 'foobar'},
                                       self.backend)
        self._setup_handlers()
        self.do_partial_pipeline()

    def test_failed_login(self):
        self._setup_handlers()
        with self.assertRaises(AuthMissingParameter):
            self.do_login()
