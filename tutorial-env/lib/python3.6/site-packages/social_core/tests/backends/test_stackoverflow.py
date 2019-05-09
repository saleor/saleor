import json

from six.moves.urllib_parse import urlencode

from .oauth import OAuth2Test


class StackoverflowOAuth2Test(OAuth2Test):
    backend_path = 'social_core.backends.stackoverflow.StackoverflowOAuth2'
    user_data_url = 'https://api.stackexchange.com/2.1/me'
    expected_username = 'foobar'
    access_token_body = urlencode({
        'access_token': 'foobar',
        'token_type': 'bearer'
    })
    user_data_body = json.dumps({
        'items': [{
            'user_id': 101010,
            'user_type': 'registered',
            'creation_date': 1278525551,
            'display_name': 'foobar',
            'profile_image': 'http: //www.gravatar.com/avatar/'
                             '5280f15cedf540b544eecc30fcf3027c?'
                             'd=identicon&r=PG',
            'reputation': 547,
            'reputation_change_day': 0,
            'reputation_change_week': 0,
            'reputation_change_month': 0,
            'reputation_change_quarter': 65,
            'reputation_change_year': 65,
            'age': 22,
            'last_access_date': 1363544705,
            'last_modified_date': 1354035327,
            'is_employee': False,
            'link': 'http: //stackoverflow.com/users/101010/foobar',
            'location': 'Fooland',
            'account_id': 101010,
            'badge_counts': {
                'gold': 0,
                'silver': 3,
                'bronze': 6
            }
        }],
        'quota_remaining': 9997,
        'quota_max': 10000,
        'has_more': False
    })

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()
