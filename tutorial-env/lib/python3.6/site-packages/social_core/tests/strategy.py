from ..strategy import BaseStrategy, BaseTemplateStrategy


TEST_URI = 'http://myapp.com'
TEST_HOST = 'myapp.com'


class Redirect(object):
    def __init__(self, url):
        self.url = url


class TestTemplateStrategy(BaseTemplateStrategy):
    def render_template(self, tpl, context):
        return tpl

    def render_string(self, html, context):
        return html


class TestStrategy(BaseStrategy):
    DEFAULT_TEMPLATE_STRATEGY = TestTemplateStrategy

    def __init__(self, storage, tpl=None):
        self._request_data = {}
        self._settings = {}
        self._session = {}
        super(TestStrategy, self).__init__(storage, tpl)

    def redirect(self, url):
        return Redirect(url)

    def get_setting(self, name):
        """Return value for given setting name"""
        return self._settings[name]

    def html(self, content):
        """Return HTTP response with given content"""
        return content

    def render_html(self, tpl=None, html=None, context=None):
        """Render given template or raw html with given context"""
        return tpl or html

    def request_data(self, merge=True):
        """Return current request data (POST or GET)"""
        return self._request_data

    def request_host(self):
        """Return current host value"""
        return TEST_HOST

    def request_is_secure(self):
        """ Is the request using HTTPS? """
        return False

    def request_path(self):
        """ path of the current request """
        return ''

    def request_port(self):
        """ Port in use for this request """
        return 80

    def request_get(self):
        """ Request GET data """
        return self._request_data.copy()

    def request_post(self):
        """ Request POST data """
        return self._request_data.copy()

    def session_get(self, name, default=None):
        """Return session value for given key"""
        return self._session.get(name, default)

    def session_set(self, name, value):
        """Set session value for given key"""
        self._session[name] = value

    def session_pop(self, name):
        """Pop session value for given key"""
        return self._session.pop(name, None)

    def build_absolute_uri(self, path=None):
        """Build absolute URI with given (optional) path"""
        path = path or ''
        if path.startswith('http://') or path.startswith('https://'):
            return path
        return TEST_URI + path

    def set_settings(self, values):
        self._settings.update(values)

    def set_request_data(self, values, backend):
        self._request_data.update(values)
        backend.data = self._request_data

    def remove_from_request_data(self, name):
        self._request_data.pop(name, None)

    def authenticate(self, *args, **kwargs):
        user = super(TestStrategy, self).authenticate(*args, **kwargs)
        if isinstance(user, self.storage.user.user_model()):
            self.session_set('username', user.username)
        return user

    def get_pipeline(self, backend=None):
        return self.setting(
            'PIPELINE',
            (
                'social_core.pipeline.social_auth.social_details',
                'social_core.pipeline.social_auth.social_uid',
                'social_core.pipeline.social_auth.auth_allowed',
                'social_core.pipeline.social_auth.social_user',
                'social_core.pipeline.user.get_username',
                'social_core.pipeline.social_auth.associate_by_email',
                'social_core.pipeline.user.create_user',
                'social_core.pipeline.social_auth.associate_user',
                'social_core.pipeline.social_auth.load_extra_data',
                'social_core.pipeline.user.user_details'
            ),
            backend
        )
