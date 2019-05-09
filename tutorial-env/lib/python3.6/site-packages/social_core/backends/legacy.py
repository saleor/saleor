from .base import BaseAuth
from ..exceptions import AuthMissingParameter


class LegacyAuth(BaseAuth):
    def get_user_id(self, details, response):
        return details.get(self.ID_KEY) or \
               response.get(self.ID_KEY)

    def auth_url(self):
        return self.setting('FORM_URL')

    def auth_html(self):
        return self.strategy.render_html(tpl=self.setting('FORM_HTML'))

    def uses_redirect(self):
        return self.setting('FORM_URL') and not \
               self.setting('FORM_HTML')

    def auth_complete(self, *args, **kwargs):
        """Completes login process, must return user instance"""
        if self.ID_KEY not in self.data:
            raise AuthMissingParameter(self, self.ID_KEY)
        kwargs.update({'response': self.data, 'backend': self})
        return self.strategy.authenticate(*args, **kwargs)

    def get_user_details(self, response):
        """Return user details"""
        email = response.get('email', '')
        username = response.get('username', '')
        fullname, first_name, last_name = self.get_user_names(
            response.get('fullname', ''),
            response.get('first_name', ''),
            response.get('last_name', '')
        )
        if email and not username:
            username = email.split('@', 1)[0]
        return {
            'username': username,
            'email': email,
            'fullname': fullname,
            'first_name': first_name,
            'last_name': last_name
        }
