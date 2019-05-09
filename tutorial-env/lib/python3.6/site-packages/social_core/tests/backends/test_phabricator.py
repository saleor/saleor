import json

from .oauth import OAuth2Test


class PhabricatorOAuth2Test(OAuth2Test):
    backend_path = 'social_core.backends.phabricator.PhabricatorOAuth2'
    user_data_url = 'https://secure.phabricator.com/api/user.whoami'
    expected_username = 'user'
    access_token_body = json.dumps({
        'access_token': 'loremipsumdolorsitametenim',
        'token_type': 'Bearer',
        'expires_in': 7200,
        'refresh_token': 'foobar',
    })

    user_data_body = json.dumps({
        'phid': 'PHID-USER-jbfcsj7c6nkt2tv3trb6',
        'userName': 'user',
        'realName': 'FirstName LastName',
        'image': 'https://secure.phabricator.com/file/data/4qjdpmvca4wwkfw2wevc'
                 '/PHID-FILE-t37vxezr54fjuvbrblkp/alphanumeric_lato-white_U.png'
                 '-_3f674d-255%2C255%2C255%2C0.7.png',
        'uri': 'https://secure.phabricator.com/p/user/',
        'roles': ['admin', 'verified', 'approved', 'activated'],
        'primaryEmail': 'user@example.com',
    })

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()


class PhabricatorCustomDomainOAuth2Test(OAuth2Test):
    backend_path = 'social_core.backends.phabricator.PhabricatorOAuth2'
    user_data_url = 'https://example.com/api/user.whoami'
    expected_username = 'user'
    access_token_body = json.dumps({
        'access_token': 'loremipsumdolorsitametenim',
        'token_type': 'Bearer',
        'expires_in': 7200,
        'refresh_token': 'foobar',
    })

    user_data_body = json.dumps({
        'phid': 'PHID-USER-jbfcsj7c6nkt2tv3trb6',
        'userName': 'user',
        'realName': 'FirstName LastName',
        'image': 'https://example.com/file/data/4qjdpmvca4wwkfw2wevc/PHID-FILE-'
                 't37vxezr54fjuvbrblkp/alphanumeric_lato-white_U.png-_3f674d-25'
                 '5%2C255%2C255%2C0.7.png',
        'uri': 'https://example.com/p/user/',
        'roles': ['admin', 'verified', 'approved', 'activated'],
        'primaryEmail': 'user@example.com',
    })

    def test_login(self):
        self.strategy.set_settings({
            'SOCIAL_AUTH_PHABRICATOR_API_URL': 'https://example.com',
        })
        self.do_login()

    def test_partial_pipeline(self):
        self.strategy.set_settings({
            'SOCIAL_AUTH_PHABRICATOR_API_URL': 'https://example.com',
        })
        self.do_partial_pipeline()
