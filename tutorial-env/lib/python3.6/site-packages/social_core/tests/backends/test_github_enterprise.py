import json

from httpretty import HTTPretty

from ...exceptions import AuthFailed

from .oauth import OAuth2Test


class GithubEnterpriseOAuth2Test(OAuth2Test):
    backend_path = 'social_core.backends.github_enterprise.GithubEnterpriseOAuth2'
    user_data_url = 'https://www.example.com/api/v3/user'
    expected_username = 'foobar'
    access_token_body = json.dumps({
        'access_token': 'foobar',
        'token_type': 'bearer'
    })
    user_data_body = json.dumps({
        'login': 'foobar',
        'id': 1,
        'avatar_url': 'https://www.example.com/images/error/foobar_happy.gif',
        'gravatar_id': 'somehexcode',
        'url': 'https://www.example.com/api/v3/users/foobar',
        'name': 'monalisa foobar',
        'company': 'GitHub',
        'blog': 'https://www.example.com/blog',
        'location': 'San Francisco',
        'email': 'foo@bar.com',
        'hireable': False,
        'bio': 'There once was...',
        'public_repos': 2,
        'public_gists': 1,
        'followers': 20,
        'following': 0,
        'html_url': 'https://www.example.com/foobar',
        'created_at': '2008-01-14T04:33:35Z',
        'type': 'User',
        'total_private_repos': 100,
        'owned_private_repos': 100,
        'private_gists': 81,
        'disk_usage': 10000,
        'collaborators': 8,
        'plan': {
            'name': 'Medium',
            'space': 400,
            'collaborators': 10,
            'private_repos': 20
        }
    })

    def test_login(self):
        self.strategy.set_settings({
            'SOCIAL_AUTH_GITHUB_ENTERPRISE_URL': 'https://www.example.com'})
        self.strategy.set_settings({
            'SOCIAL_AUTH_GITHUB_ENTERPRISE_API_URL': 'https://www.example.com/api/v3'})
        self.do_login()

    def test_partial_pipeline(self):
        self.strategy.set_settings({
            'SOCIAL_AUTH_GITHUB_ENTERPRISE_URL': 'https://www.example.com'})
        self.strategy.set_settings({
            'SOCIAL_AUTH_GITHUB_ENTERPRISE_API_URL': 'https://www.example.com/api/v3'})
        self.do_partial_pipeline()


class GithubEnterpriseOAuth2NoEmailTest(GithubEnterpriseOAuth2Test):
    user_data_body = json.dumps({
        'login': 'foobar',
        'id': 1,
        'avatar_url': 'https://www.example.com/images/error/foobar_happy.gif',
        'gravatar_id': 'somehexcode',
        'url': 'https://www.example.com/api/v3/users/foobar',
        'name': 'monalisa foobar',
        'company': 'GitHub',
        'blog': 'https://www.example.com/blog',
        'location': 'San Francisco',
        'email': '',
        'hireable': False,
        'bio': 'There once was...',
        'public_repos': 2,
        'public_gists': 1,
        'followers': 20,
        'following': 0,
        'html_url': 'https://www.example.com/foobar',
        'created_at': '2008-01-14T04:33:35Z',
        'type': 'User',
        'total_private_repos': 100,
        'owned_private_repos': 100,
        'private_gists': 81,
        'disk_usage': 10000,
        'collaborators': 8,
        'plan': {
            'name': 'Medium',
            'space': 400,
            'collaborators': 10,
            'private_repos': 20
        }
    })

    def test_login(self):
        self.strategy.set_settings({
            'SOCIAL_AUTH_GITHUB_ENTERPRISE_URL': 'https://www.example.com'})
        self.strategy.set_settings({
            'SOCIAL_AUTH_GITHUB_ENTERPRISE_API_URL': 'https://www.example.com/api/v3'})
        url = 'https://www.example.com/api/v3/user/emails'
        HTTPretty.register_uri(HTTPretty.GET, url, status=200,
                               body=json.dumps(['foo@bar.com']),
                               content_type='application/json')
        self.do_login()

    def test_login_next_format(self):
        self.strategy.set_settings({
            'SOCIAL_AUTH_GITHUB_ENTERPRISE_URL': 'https://www.example.com'})
        self.strategy.set_settings({
            'SOCIAL_AUTH_GITHUB_ENTERPRISE_API_URL': 'https://www.example.com/api/v3'})
        url = 'https://www.example.com/api/v3/user/emails'
        HTTPretty.register_uri(HTTPretty.GET, url, status=200,
                               body=json.dumps([{'email': 'foo@bar.com'}]),
                               content_type='application/json')
        self.do_login()

    def test_partial_pipeline(self):
        self.strategy.set_settings({
            'SOCIAL_AUTH_GITHUB_ENTERPRISE_URL': 'https://www.example.com'})
        self.strategy.set_settings({
            'SOCIAL_AUTH_GITHUB_ENTERPRISE_API_URL': 'https://www.example.com/api/v3'})
        self.do_partial_pipeline()


class GithubEnterpriseOrganizationOAuth2Test(GithubEnterpriseOAuth2Test):
    backend_path = 'social_core.backends.github_enterprise.GithubEnterpriseOrganizationOAuth2'

    def auth_handlers(self, start_url):
        url = 'https://www.example.com/api/v3/orgs/foobar/members/foobar'
        HTTPretty.register_uri(HTTPretty.GET, url, status=204, body='')
        return super(GithubEnterpriseOrganizationOAuth2Test, self).auth_handlers(
            start_url
        )

    def test_login(self):
        self.strategy.set_settings({
            'SOCIAL_AUTH_GITHUB_ENTERPRISE_ORG_URL': 'https://www.example.com'})
        self.strategy.set_settings({
            'SOCIAL_AUTH_GITHUB_ENTERPRISE_ORG_API_URL': 'https://www.example.com/api/v3'})
        self.strategy.set_settings({'SOCIAL_AUTH_GITHUB_ENTERPRISE_ORG_NAME': 'foobar'})
        self.do_login()

    def test_partial_pipeline(self):
        self.strategy.set_settings({
            'SOCIAL_AUTH_GITHUB_ENTERPRISE_ORG_URL': 'https://www.example.com'})
        self.strategy.set_settings({
            'SOCIAL_AUTH_GITHUB_ENTERPRISE_ORG_API_URL': 'https://www.example.com/api/v3'})
        self.strategy.set_settings({'SOCIAL_AUTH_GITHUB_ENTERPRISE_ORG_NAME': 'foobar'})
        self.do_partial_pipeline()


class GithubEnterpriseOrganizationOAuth2FailTest(GithubEnterpriseOAuth2Test):
    backend_path = 'social_core.backends.github_enterprise.GithubEnterpriseOrganizationOAuth2'

    def auth_handlers(self, start_url):
        url = 'https://www.example.com/api/v3/orgs/foobar/members/foobar'
        HTTPretty.register_uri(HTTPretty.GET, url, status=404,
                               body='{"message": "Not Found"}',
                               content_type='application/json')
        return super(GithubEnterpriseOrganizationOAuth2FailTest, self).auth_handlers(
            start_url
        )

    def test_login(self):
        self.strategy.set_settings({
            'SOCIAL_AUTH_GITHUB_ENTERPRISE_ORG_URL': 'https://www.example.com'})
        self.strategy.set_settings({
            'SOCIAL_AUTH_GITHUB_ENTERPRISE_ORG_API_URL': 'https://www.example.com/api/v3'})
        self.strategy.set_settings({'SOCIAL_AUTH_GITHUB_ENTERPRISE_ORG_NAME': 'foobar'})
        with self.assertRaises(AuthFailed):
            self.do_login()

    def test_partial_pipeline(self):
        self.strategy.set_settings({
            'SOCIAL_AUTH_GITHUB_ENTERPRISE_ORG_URL': 'https://www.example.com'})
        self.strategy.set_settings({
            'SOCIAL_AUTH_GITHUB_ENTERPRISE_ORG_API_URL': 'https://www.example.com/api/v3'})
        self.strategy.set_settings({'SOCIAL_AUTH_GITHUB_ENTERPRISE_ORG_NAME': 'foobar'})
        with self.assertRaises(AuthFailed):
            self.do_partial_pipeline()


class GithubEnterpriseTeamOAuth2Test(GithubEnterpriseOAuth2Test):
    backend_path = 'social_core.backends.github_enterprise.GithubEnterpriseTeamOAuth2'

    def auth_handlers(self, start_url):
        url = 'https://www.example.com/api/v3/teams/123/members/foobar'
        HTTPretty.register_uri(HTTPretty.GET, url, status=204, body='')
        return super(GithubEnterpriseTeamOAuth2Test, self).auth_handlers(
            start_url
        )

    def test_login(self):
        self.strategy.set_settings({
            'SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_URL': 'https://www.example.com'})
        self.strategy.set_settings({
            'SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_API_URL': 'https://www.example.com/api/v3'})
        self.strategy.set_settings({'SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_ID': '123'})
        self.do_login()

    def test_partial_pipeline(self):
        self.strategy.set_settings({
            'SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_URL': 'https://www.example.com'})
        self.strategy.set_settings({
            'SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_API_URL': 'https://www.example.com/api/v3'})
        self.strategy.set_settings({'SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_ID': '123'})
        self.do_partial_pipeline()


class GithubEnterpriseTeamOAuth2FailTest(GithubEnterpriseOAuth2Test):
    backend_path = 'social_core.backends.github_enterprise.GithubEnterpriseTeamOAuth2'

    def auth_handlers(self, start_url):
        url = 'https://www.example.com/api/v3/teams/123/members/foobar'
        HTTPretty.register_uri(HTTPretty.GET, url, status=404,
                               body='{"message": "Not Found"}',
                               content_type='application/json')
        return super(GithubEnterpriseTeamOAuth2FailTest, self).auth_handlers(
            start_url
        )

    def test_login(self):
        self.strategy.set_settings({
            'SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_URL': 'https://www.example.com'})
        self.strategy.set_settings({
            'SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_API_URL': 'https://www.example.com/api/v3'})
        self.strategy.set_settings({'SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_ID': '123'})
        with self.assertRaises(AuthFailed):
            self.do_login()

    def test_partial_pipeline(self):
        self.strategy.set_settings({
            'SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_URL': 'https://www.example.com'})
        self.strategy.set_settings({
            'SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_API_URL': 'https://www.example.com/api/v3'})
        self.strategy.set_settings({'SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_ID': '123'})
        with self.assertRaises(AuthFailed):
            self.do_partial_pipeline()
