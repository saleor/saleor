import json

from .oauth import OAuth2Test


class FlatOAuth2Test(OAuth2Test):
    backend_path = 'social_core.backends.flat.FlatOAuth2'
    user_data_url = 'https://api.flat.io/v2/me'
    expected_username = 'vincent'
    access_token_body = json.dumps({
        'access_token': 'foobar',
        'token_type': 'bearer'
    })
    user_data_body = json.dumps({
        "id": "541a137946fd04d57cb2e3c0",
        "username": "vincent",
        "name": "Vincent Foo",
        "printableName": "Vincent Foo",
        "bio": "Foo bio",
        "instruments": [],
        "picture": "https://flat-prod-public.s3.amazonaws.com/00000000/a0d2cb86-ab1e-4fdb-9286-dd94aa6d386c.jpeg",
        "registrationDate": "2014-09-17T23:04:25.042Z",
        "htmlUrl": "https://flat.io/vincent",
        "starredScoresCount": 85,
        "likedScoresCount": 85,
        "followersCount": 183,
        "followingCount": 52,
        "ownedPublicScoresCount": 15,
        "isPowerUser": True
    })

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()