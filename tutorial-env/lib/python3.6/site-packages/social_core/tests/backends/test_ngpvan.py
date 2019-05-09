"""Tests for NGP VAN ActionID Backend"""
import datetime

from httpretty import HTTPretty

from six.moves.urllib_parse import urlencode

from .open_id import OpenIdTest


JANRAIN_NONCE = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')


class NGPVANActionIDOpenIDTest(OpenIdTest):
    """Test the NGP VAN ActionID OpenID 1.1 Backend"""
    backend_path = 'social_core.backends.ngpvan.ActionIDOpenID'
    expected_username = 'testuser@user.local'
    discovery_body = ' '.join([
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<xrds:XRDS',
        'xmlns:xrds="xri://$xrds"',
        'xmlns:openid="http://openid.net/xmlns/1.0"',
        'xmlns="xri://$xrd*($v*2.0)">',
        '<XRD>',
        '<Service priority="10">',
        '<Type>http://specs.openid.net/auth/2.0/signon</Type>',
        '<Type>http://openid.net/extensions/sreg/1.1</Type>',
        '<Type>http://axschema.org/contact/email</Type>',
        '<URI>https://accounts.ngpvan.com/OpenId/Provider</URI>',
        '</Service>',
        '<Service priority="20">',
        '<Type>http://openid.net/signon/1.0</Type>',
        '<Type>http://openid.net/extensions/sreg/1.1</Type>',
        '<Type>http://axschema.org/contact/email</Type>',
        '<URI>https://accounts.ngpvan.com/OpenId/Provider</URI>',
        '</Service>',
        '</XRD>',
        '</xrds:XRDS>'
    ])
    server_response = urlencode({
        'openid.claimed_id': 'https://accounts.ngpvan.com/user/abcd123',
        'openid.identity': 'https://accounts.ngpvan.com/user/abcd123',
        'openid.sig': 'Midw8F/rCDwW7vMz3y+vK6rjz6s=',
        'openid.signed': 'claimed_id,identity,assoc_handle,op_endpoint,return_'
                         'to,response_nonce,ns.alias3,alias3.mode,alias3.type.'
                         'alias1,alias3.value.alias1,alias3.type.alias2,alias3'
                         '.value.alias2,alias3.type.alias3,alias3.value.alias3'
                         ',alias3.type.alias4,alias3.value.alias4,alias3.type.'
                         'alias5,alias3.value.alias5,alias3.type.alias6,alias3'
                         '.value.alias6,alias3.type.alias7,alias3.value.alias7'
                         ',alias3.type.alias8,alias3.value.alias8,ns.sreg,sreg'
                         '.fullname',
        'openid.assoc_handle': '{635790678917902781}{GdSyFA==}{20}',
        'openid.op_endpoint': 'https://accounts.ngpvan.com/OpenId/Provider',
        'openid.return_to': 'http://myapp.com/complete/actionid-openid/',
        'openid.response_nonce': JANRAIN_NONCE + 'MMgBGEre',
        'openid.mode': 'id_res',
        'openid.ns': 'http://specs.openid.net/auth/2.0',
        'openid.ns.alias3': 'http://openid.net/srv/ax/1.0',
        'openid.alias3.mode': 'fetch_response',
        'openid.alias3.type.alias1': 'http://openid.net/schema/contact/phone/b'
                                     'usiness',
        'openid.alias3.value.alias1': '+12015555555',
        'openid.alias3.type.alias2': 'http://openid.net/schema/contact/interne'
                                     't/email',
        'openid.alias3.value.alias2': 'testuser@user.local',
        'openid.alias3.type.alias3': 'http://openid.net/schema/namePerson/firs'
                                     't',
        'openid.alias3.value.alias3': 'John',
        'openid.alias3.type.alias4': 'http://openid.net/schema/namePerson/las'
                                     't',
        'openid.alias3.value.alias4': 'Smith',
        'openid.alias3.type.alias5': 'http://axschema.org/namePerson/first',
        'openid.alias3.value.alias5': 'John',
        'openid.alias3.type.alias6': 'http://axschema.org/namePerson/last',
        'openid.alias3.value.alias6': 'Smith',
        'openid.alias3.type.alias7': 'http://axschema.org/namePerson',
        'openid.alias3.value.alias7': 'John Smith',
        'openid.alias3.type.alias8': 'http://openid.net/schema/namePerson',
        'openid.alias3.value.alias8': 'John Smith',
        'openid.ns.sreg': 'http://openid.net/extensions/sreg/1.1',
        'openid.sreg.fullname': 'John Smith',
    })

    def setUp(self):
        """Setup the test"""
        super(NGPVANActionIDOpenIDTest, self).setUp()

        # Mock out the NGP VAN endpoints
        HTTPretty.register_uri(
            HTTPretty.POST,
            'https://accounts.ngpvan.com/Home/Xrds',
            status=200,
            body=self.discovery_body
        )
        HTTPretty.register_uri(
            HTTPretty.GET,
            'https://accounts.ngpvan.com/user/abcd123',
            status=200,
            body=self.discovery_body
        )
        HTTPretty.register_uri(
            HTTPretty.GET,
            'https://accounts.ngpvan.com/OpenId/Provider',
            status=200,
            body=self.discovery_body
        )

    def test_login(self):
        """Test the login flow using python-social-auth's built in test"""
        self.do_login()

    def test_partial_pipeline(self):
        """Test the partial flow using python-social-auth's built in test"""
        self.do_partial_pipeline()

    def test_get_ax_attributes(self):
        """Test that the AX attributes that NGP VAN responds with are present"""
        records = self.backend.get_ax_attributes()

        self.assertEqual(records, [
            ('http://openid.net/schema/contact/internet/email', 'email'),
            ('http://openid.net/schema/contact/phone/business', 'phone'),
            ('http://openid.net/schema/namePerson/first', 'first_name'),
            ('http://openid.net/schema/namePerson/last', 'last_name'),
            ('http://openid.net/schema/namePerson', 'fullname'),
        ])

    def test_setup_request(self):
        """Test the setup_request functionality in the NGP VAN backend"""
        # We can grab the requested attributes by grabbing the HTML of the
        # OpenID auth form and pulling out the hidden fields
        _, inputs = self.get_form_data(self.backend.auth_html())

        # Confirm that the only required attribute is email
        self.assertEqual(inputs['openid.ax.required'], 'ngpvanemail')

        # Confirm that the 3 optional attributes are requested "if available"
        self.assertIn('ngpvanphone', inputs['openid.ax.if_available'])
        self.assertIn('ngpvanfirstname', inputs['openid.ax.if_available'])
        self.assertIn('ngpvanlastname', inputs['openid.ax.if_available'])

        # Verify the individual attribute properties
        self.assertEqual(
            inputs['openid.ax.type.ngpvanemail'],
            'http://openid.net/schema/contact/internet/email'
        )
        self.assertEqual(
            inputs['openid.ax.type.ngpvanfirstname'],
            'http://openid.net/schema/namePerson/first'
        )
        self.assertEqual(
            inputs['openid.ax.type.ngpvanlastname'],
            'http://openid.net/schema/namePerson/last'
        )
        self.assertEqual(
            inputs['openid.ax.type.ngpvanphone'],
            'http://openid.net/schema/contact/phone/business'
        )

    def test_user_data(self):
        """Ensure that the correct user data is being passed to create_user"""
        self.strategy.set_settings({
            'USER_FIELDS': [
                'email',
                'first_name',
                'last_name',
                'username',
                'phone',
                'fullname'
            ]
        })
        user = self.do_start()
        self.assertEqual(user.username, u'testuser@user.local')
        self.assertEqual(user.email, u'testuser@user.local')
        self.assertEqual(user.extra_user_fields['phone'], u'+12015555555')
        self.assertEqual(user.extra_user_fields['first_name'], u'John')
        self.assertEqual(user.extra_user_fields['last_name'], u'Smith')
        self.assertEqual(user.extra_user_fields['fullname'], u'John Smith')

    def test_extra_data_phone(self):
        """Confirm that you can get a phone number via the relevant setting"""
        self.strategy.set_settings({
            'SOCIAL_AUTH_ACTIONID_OPENID_AX_EXTRA_DATA': [
                ('http://openid.net/schema/contact/phone/business', 'phone')
            ]
        })
        user = self.do_start()
        self.assertEqual(user.social_user.extra_data['phone'], u'+12015555555')

    def test_association_uid(self):
        """Test that the correct association uid is stored in the database"""
        user = self.do_start()
        self.assertEqual(
            user.social_user.uid,
            'https://accounts.ngpvan.com/user/abcd123'
        )
