import json

from .oauth import OAuth2Test


class SlackOAuth2Test(OAuth2Test):
    backend_path = 'social_core.backends.slack.SlackOAuth2'
    user_data_url = 'https://slack.com/api/users.identity'
    access_token_body = json.dumps({
        'access_token': 'foobar',
        'token_type': 'bearer'
    })
    user_data_body = json.dumps({
        'ok': True,
        'user': {
            'email': 'foobar@example.com',
            'name': 'Foo Bar',
            'id': u'123456'
        },
        'team': {
            'id': u'456789'
        },
        'scope': u'identity.basic,identity.email'
    })
    expected_username = 'foobar'

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()


class SlackOAuth2TestTeamName(SlackOAuth2Test):
    expected_username = 'foobar@Square'
    user_data_body = json.dumps({
        'ok': True,
        'user': {
            'email': 'foobar@example.com',
            'name': 'Foo Bar',
            'id': u'123456'
        },
        'team': {
            'id': u'456789',
            'name': u'Square',
        },
        'scope': u'identity.basic,identity.email,identity.team'
    })


class SlackOAuth2TestUnicodeTeamName(SlackOAuth2Test):
    user_data_body = json.dumps({
        'ok': True,
        'user': {
            'email': 'foobar@example.com',
            'name': 'Foo Bar',
            'id': u'123456'
        },
        'team': {
            'id': u'456789',
            'name': u'Square \u221a team',
        },
        'scope': u'identity.basic,identity.email,identity.team'
    })

    def test_login(self):
        self.strategy.set_settings({
            'SOCIAL_AUTH_SLACK_USERNAME_WITH_TEAM': False
        })
        self.do_login()

    def test_partial_pipeline(self):
        self.strategy.set_settings({
            'SOCIAL_AUTH_SLACK_USERNAME_WITH_TEAM': False
        })
        self.do_partial_pipeline()
