from .legacy import BaseLegacyTest


class UsernameTest(BaseLegacyTest):
    backend_path = 'social_core.backends.username.UsernameAuth'
    expected_username = 'foobar'
    response_body = 'username=foobar'
    form = """
    <form method="post" action="{0}">
        <input name="username" type="text">
        <button>Submit</button>
    </form>
    """

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()
