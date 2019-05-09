import datetime

from .oauth import BaseOAuth2


class AsanaOAuth2(BaseOAuth2):
    name = 'asana'
    AUTHORIZATION_URL = 'https://app.asana.com/-/oauth_authorize'
    ACCESS_TOKEN_METHOD = 'POST'
    ACCESS_TOKEN_URL = 'https://app.asana.com/-/oauth_token'
    REFRESH_TOKEN_URL = 'https://app.asana.com/-/oauth_token'
    REDIRECT_STATE = False
    USER_DATA_URL = 'https://app.asana.com/api/1.0/users/me'
    EXTRA_DATA = [
        ('expires_in', 'expires'),
        ('refresh_token', 'refresh_token'),
        ('name', 'name'),
    ]

    def get_user_details(self, response):
        data = response['data']
        fullname, first_name, last_name = self.get_user_names(data['name'])
        return {'email': data['email'],
                'username': data['email'],
                'fullname': fullname,
                'last_name': last_name,
                'first_name': first_name}

    def user_data(self, access_token, *args, **kwargs):
        return self.get_json(self.USER_DATA_URL, headers={
            'Authorization': 'Bearer {}'.format(access_token)
        })

    def extra_data(self, user, uid, response, details=None, *args, **kwargs):
        data = super(AsanaOAuth2, self).extra_data(
            user, uid, response, details
        )
        if self.setting('ESTIMATE_EXPIRES_ON'):
            expires_on = datetime.datetime.utcnow() + \
                         datetime.timedelta(seconds=data['expires'])
            data['expires_on'] = expires_on.isoformat()
        return data
