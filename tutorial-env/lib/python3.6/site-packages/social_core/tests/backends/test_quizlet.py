import json

from .oauth import OAuth2Test


class QuizletOAuth2Test(OAuth2Test):
    backend_path = 'social_core.backends.quizlet.QuizletOAuth2'
    expected_username = 'foo_bar'

    access_token_body = json.dumps({
        "access_token": "EE1IDxytP04tJ767GbjH7ED9PpGmYvL",
        "token_type": "Bearer",
        "expires_in": 3600,
        "scope": "read",
        'user_id': 'foo_bar'
    })

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()
