import hmac
import time
import hashlib

from .base import BaseAuth
from ..exceptions import AuthFailed, AuthMissingParameter
from ..utils import handle_http_errors


class TelegramAuth(BaseAuth):
    name = 'telegram'
    ID_KEY = 'id'

    def verify_data(self, response):
        bot_token = self.setting('BOT_TOKEN')
        if bot_token is None:
            raise AuthMissingParameter('telegram',
                                       'SOCIAL_AUTH_TELEGRAM_BOT_TOKEN')

        received_hash_string = response.get('hash')
        auth_date = response.get('auth_date')

        if received_hash_string is None or auth_date is None:
            raise AuthMissingParameter('telegram', 'hash or auth_date')

        data_check_string = ['{}={}'.format(k, v)
                             for k, v in response.items() if k != 'hash']
        data_check_string = '\n'.join(sorted(data_check_string))
        secret_key = hashlib.sha256(bot_token.encode()).digest()
        built_hash = hmac.new(secret_key,
                              msg=data_check_string.encode(),
                              digestmod=hashlib.sha256).hexdigest()
        current_timestamp = int(time.time())
        auth_timestamp = int(auth_date)
        if current_timestamp - auth_timestamp > 86400:
            raise AuthFailed('telegram', 'Auth date is outdated')
        if built_hash != received_hash_string:
            raise AuthFailed('telegram', 'Invalid hash supplied')

    def extra_data(self, user, uid, response, details=None, *args, **kwargs):
        return response

    def get_user_details(self, response):
        first_name = response.get('first_name', '')
        last_name = response.get('last_name', '')
        fullname = '{} {}'.format(first_name, last_name).strip()
        return {
            'username': response.get('username') or response[self.ID_KEY],
            'first_name': first_name,
            'last_name': last_name,
            'fullname': fullname
        }

    @handle_http_errors
    def auth_complete(self, *args, **kwargs):
        response = self.data
        self.verify_data(response)
        kwargs.update({'response': self.data, 'backend': self})
        return self.strategy.authenticate(*args, **kwargs)
