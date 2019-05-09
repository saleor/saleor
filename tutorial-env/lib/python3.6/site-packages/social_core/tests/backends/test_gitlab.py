import json

from httpretty import HTTPretty

from ...exceptions import AuthFailed

from .oauth import OAuth2Test


class GitLabOAuth2Test(OAuth2Test):
    backend_path = 'social_core.backends.gitlab.GitLabOAuth2'
    user_data_url = 'https://gitlab.com/api/v4/user'
    expected_username = 'foobar'
    access_token_body = json.dumps({
        'access_token': 'foobar',
        'token_type': 'bearer',
        'expires_in': 7200,
        'refresh_token': 'barfoo'
    })
    user_data_body = json.dumps({
        'two_factor_enabled': False,
        'can_create_project': True,
        'confirmed_at': '2016-12-28T12:26:19.256Z',
        'twitter': '',
        'linkedin': '',
        'color_scheme_id': 1,
        'web_url': 'https://gitlab.com/foobar',
        'skype': '',
        'identities': [],
        'id': 123456,
        'projects_limit': 100000,
        'current_sign_in_at': '2016-12-28T12:26:19.795Z',
        'state': 'active',
        'location': None,
        'email': 'foobar@example.com',
        'website_url': '',
        'username': 'foobar',
        'bio': None,
        'last_sign_in_at': '2016-12-28T12:26:19.795Z',
        'is_admin': False,
        'external': False,
        'organization': None,
        'name': 'Foo Bar',
        'can_create_group': True,
        'created_at': '2016-12-28T12:26:19.638Z',
        'avatar_url': 'https://secure.gravatar.com/avatar/94d093eda664addd6e450d7e9881bcae?s=32&d=identicon',
        'theme_id': 2
    })

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()


class GitLabCustomDomainOAuth2Test(OAuth2Test):
    backend_path = 'social_core.backends.gitlab.GitLabOAuth2'
    user_data_url = 'https://example.com/api/v4/user'
    expected_username = 'foobar'
    access_token_body = json.dumps({
        'access_token': 'foobar',
        'token_type': 'bearer',
        'expires_in': 7200,
        'refresh_token': 'barfoo'
    })
    user_data_body = json.dumps({
        'two_factor_enabled': False,
        'can_create_project': True,
        'confirmed_at': '2016-12-28T12:26:19.256Z',
        'twitter': '',
        'linkedin': '',
        'color_scheme_id': 1,
        'web_url': 'https://example.com/foobar',
        'skype': '',
        'identities': [],
        'id': 123456,
        'projects_limit': 100000,
        'current_sign_in_at': '2016-12-28T12:26:19.795Z',
        'state': 'active',
        'location': None,
        'email': 'foobar@example.com',
        'website_url': '',
        'username': 'foobar',
        'bio': None,
        'last_sign_in_at': '2016-12-28T12:26:19.795Z',
        'is_admin': False,
        'external': False,
        'organization': None,
        'name': 'Foo Bar',
        'can_create_group': True,
        'created_at': '2016-12-28T12:26:19.638Z',
        'avatar_url': 'https://secure.gravatar.com/avatar/94d093eda664addd6e450d7e9881bcae?s=32&d=identicon',
        'theme_id': 2
    })

    def test_login(self):
        self.strategy.set_settings({
            'SOCIAL_AUTH_GITLAB_API_URL': 'https://example.com'
        })
        self.do_login()

    def test_partial_pipeline(self):
        self.strategy.set_settings({
            'SOCIAL_AUTH_GITLAB_API_URL': 'https://example.com'
        })
        self.do_partial_pipeline()
