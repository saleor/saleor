import json

from .oauth import OAuth2Test


class YammerOAuth2Test(OAuth2Test):
    backend_path = 'social_core.backends.yammer.YammerOAuth2'
    expected_username = 'foobar'
    access_token_body = json.dumps({
        'access_token': {
            'user_id': 1010101010,
            'view_groups': True,
            'modify_messages': True,
            'network_id': 101010,
            'created_at': '2013/03/17 16:39:56 +0000',
            'view_members': True,
            'authorized_at': '2013/03/17 16:39:56 +0000',
            'view_subscriptions': True,
            'view_messages': True,
            'modify_subscriptions': True,
            'token': 'foobar',
            'expires_at': None,
            'network_permalink': 'foobar.com',
            'view_tags': True,
            'network_name': 'foobar.com'
        },
        'user': {
            'last_name': 'Bar',
            'web_url': 'https://www.yammer.com/foobar/users/foobar',
            'expertise': None,
            'full_name': 'Foo Bar',
            'timezone': 'Pacific Time (US & Canada)',
            'mugshot_url': 'https://mug0.assets-yammer.com/mugshot/images/'
                           '48x48/no_photo.png',
            'guid': None,
            'network_name': 'foobar',
            'id': 1010101010,
            'previous_companies': [],
            'first_name': 'Foo',
            'stats': {
                'following': 0,
                'followers': 0,
                'updates': 1
            },
            'hire_date': None,
            'state': 'active',
            'location': None,
            'department': 'Software Development',
            'type': 'user',
            'show_ask_for_photo': True,
            'job_title': 'Software Developer',
            'interests': None,
            'kids_names': None,
            'activated_at': '2013/03/17 16:27:50 +0000',
            'verified_admin': 'false',
            'can_broadcast': 'false',
            'schools': [],
            'admin': 'false',
            'network_domains': ['foobar.com'],
            'name': 'foobar',
            'external_urls': [],
            'url': 'https://www.yammer.com/api/v1/users/1010101010',
            'settings': {
                'xdr_proxy': 'https://xdrproxy.yammer.com'
            },
            'summary': None,
            'network_id': 101010,
            'contact': {
                'phone_numbers': [],
                'im': {
                    'username': '',
                    'provider': ''
                },
                'email_addresses': [{
                    'type': 'primary',
                    'address': 'foo@bar.com'
                }],
                'has_fake_email': False
            },
            'birth_date': '',
            'mugshot_url_template': 'https://mug0.assets-yammer.com/mugshot/'
                                    'images/{width}x{height}/no_photo.png',
            'significant_other': None
        },
        'network': {
            'show_upgrade_banner': False,
            'header_text_color': '#FFFFFF',
            'is_org_chart_enabled': True,
            'name': 'foobar.com',
            'is_group_enabled': True,
            'header_background_color': '#396B9A',
            'created_at': '2012/12/26 16:52:35 +0000',
            'profile_fields_config': {
                'enable_work_phone': True,
                'enable_mobile_phone': True,
                'enable_job_title': True
            },
            'permalink': 'foobar.com',
            'paid': False,
            'id': 101010,
            'is_chat_enabled': True,
            'web_url': 'https://www.yammer.com/foobar.com',
            'moderated': False,
            'community': False,
            'type': 'network',
            'navigation_background_color': '#38699F',
            'navigation_text_color': '#FFFFFF'
        }
    })

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()
