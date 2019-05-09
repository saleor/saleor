import json

from .oauth import OAuth2Test


class RedditOAuth2Test(OAuth2Test):
    backend_path = 'social_core.backends.reddit.RedditOAuth2'
    user_data_url = 'https://oauth.reddit.com/api/v1/me.json'
    expected_username = 'foobar'
    access_token_body = json.dumps({
        'name': 'foobar',
        'created': 1203420772.0,
        'access_token': 'foobar-token',
        'created_utc': 1203420772.0,
        'expires_in': 3600.0,
        'link_karma': 34,
        'token_type': 'bearer',
        'comment_karma': 167,
        'over_18': True,
        'is_gold': False,
        'is_mod': True,
        'scope': 'identity',
        'has_verified_email': False,
        'id': '33bma',
        'refresh_token': 'foobar-refresh-token'
    })
    user_data_body = json.dumps({
        'name': 'foobar',
        'created': 1203420772.0,
        'created_utc': 1203420772.0,
        'link_karma': 34,
        'comment_karma': 167,
        'over_18': True,
        'is_gold': False,
        'is_mod': True,
        'has_verified_email': False,
        'id': '33bma'
    })
    refresh_token_body = json.dumps({
        'access_token': 'foobar-new-token',
        'token_type': 'bearer',
        'expires_in': 3600.0,
        'refresh_token': 'foobar-new-refresh-token',
        'scope': 'identity'
    })

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()

    def refresh_token_arguments(self):
        uri = self.strategy.build_absolute_uri('/complete/reddit/')
        return {'redirect_uri': uri}

    def test_refresh_token(self):
        user, social = self.do_refresh_token()
        self.assertEqual(social.extra_data['access_token'], 'foobar-new-token')
