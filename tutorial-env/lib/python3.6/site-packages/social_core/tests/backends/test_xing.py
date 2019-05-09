import json

from six.moves.urllib_parse import urlencode

from .oauth import OAuth1Test


class XingOAuth1Test(OAuth1Test):
    backend_path = 'social_core.backends.xing.XingOAuth'
    user_data_url = 'https://api.xing.com/v1/users/me.json'
    expected_username = 'FooBar'
    access_token_body = urlencode({
        'access_token': 'foobar',
        'token_type': 'bearer',
        'user_id': '123456_abcdef',
        'oauth_token_secret': 'foobar-secret',
        'oauth_token': 'foobar',
    })
    request_token_body = urlencode({
        'oauth_token_secret': 'foobar-secret',
        'oauth_token': 'foobar',
        'oauth_callback_confirmed': 'true'
    })
    user_data_body = json.dumps({
        'users': [{
            'id': '123456_abcdef',
            'first_name': 'Foo',
            'last_name': 'Bar',
            'display_name': 'Foo Bar',
            'page_name': 'Foo_Bar',
            'permalink': 'https://www.xing.com/profile/Foo_Bar',
            'gender': 'm',
            'birth_date': {
                'day': 12,
                'month': 8,
                'year': 1963
            },
            'active_email': 'foo@bar.com',
            'time_zone': {
                'name': 'Europe/Copenhagen',
                'utc_offset': 2.0
            },
            'premium_services': ['SEARCH', 'PRIVATEMESSAGES'],
            'badges': ['PREMIUM', 'MODERATOR'],
            'wants': 'Nothing',
            'haves': 'Skills',
            'interests': 'Foo Foo',
            'organisation_member': 'ACM, GI',
            'languages': {
                'de': 'NATIVE',
                'en': 'FLUENT',
                'fr': None,
                'zh': 'BASIC'
            },
            'private_address': {
                'city': 'Foo',
                'country': 'DE',
                'zip_code': '20357',
                'street': 'Bar',
                'phone': '12|34|1234560',
                'fax': '||',
                'province': 'Foo',
                'email': 'foo@bar.com',
                'mobile_phone': '12|3456|1234567'
            },
            'business_address': {
                'city': 'Foo',
                'country': 'DE',
                'zip_code': '20357',
                'street': 'Bar',
                'phone': '12|34|1234569',
                'fax': '12|34|1234561',
                'province': 'Foo',
                'email': 'foo@bar.com',
                'mobile_phone': '12|345|12345678'
            },
            'web_profiles': {
                'qype': ['http://qype.de/users/foo'],
                'google_plus': ['http://plus.google.com/foo'],
                'blog': ['http://blog.example.org'],
                'homepage': ['http://example.org', 'http://other-example.org']
            },
            'instant_messaging_accounts': {
                'skype': 'foobar',
                'googletalk': 'foobar'
            },
            'professional_experience': {
                'primary_company': {
                    'name': 'XING AG',
                    'title': 'Softwareentwickler',
                    'company_size': '201-500',
                    'tag': None,
                    'url': 'http://www.xing.com',
                    'career_level': 'PROFESSIONAL_EXPERIENCED',
                    'begin_date': '2010-01',
                    'description': None,
                    'end_date': None,
                    'industry': 'AEROSPACE'
                },
                'non_primary_companies': [{
                    'name': 'Ninja Ltd.',
                    'title': 'DevOps',
                    'company_size': None,
                    'tag': 'NINJA',
                    'url': 'http://www.ninja-ltd.co.uk',
                    'career_level': None,
                    'begin_date': '2009-04',
                    'description': None,
                    'end_date': '2010-07',
                    'industry': 'ALTERNATIVE_MEDICINE'
                }, {
                    'name': None,
                    'title': 'Wiss. Mitarbeiter',
                    'company_size': None,
                    'tag': 'OFFIS',
                    'url': 'http://www.uni.de',
                    'career_level': None,
                    'begin_date': '2007',
                    'description': None,
                    'end_date': '2008',
                    'industry': 'APPAREL_AND_FASHION'
                }, {
                    'name': None,
                    'title': 'TEST NINJA',
                    'company_size': '201-500',
                    'tag': 'TESTCOMPANY',
                    'url': None,
                    'career_level': 'ENTRY_LEVEL',
                    'begin_date': '1998-12',
                    'description': None,
                    'end_date': '1999-05',
                    'industry': 'ARTS_AND_CRAFTS'
                }],
                'awards': [{
                    'name': 'Awesome Dude Of The Year',
                    'date_awarded': 2007,
                    'url': None
                }]
            },
            'educational_background': {
                'schools': [{
                    'name': 'Foo University',
                    'degree': 'MSc CE/CS',
                    'notes': None,
                    'subject': None,
                    'begin_date': '1998-08',
                    'end_date': '2005-02'
                }],
                'qualifications': ['TOEFLS', 'PADI AOWD']
            },
            'photo_urls': {
                'large': 'http://www.xing.com/img/users/e/3/d/'
                         'f94ef165a.123456,1.140x185.jpg',
                'mini_thumb': 'http://www.xing.com/img/users/e/3/d/'
                              'f94ef165a.123456,1.18x24.jpg',
                'thumb': 'http://www.xing.com/img/users/e/3/d/'
                         'f94ef165a.123456,1.30x40.jpg',
                'medium_thumb': 'http://www.xing.com/img/users/e/3/d/'
                                'f94ef165a.123456,1.57x75.jpg',
                'maxi_thumb': 'http://www.xing.com/img/users/e/3/d/'
                              'f94ef165a.123456,1.70x93.jpg'
            }
        }]
    })

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()
