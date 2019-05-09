"""
RunKeeper OAuth2 backend, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/runkeeper.html
"""
from .oauth import BaseOAuth2


class RunKeeperOAuth2(BaseOAuth2):
    """RunKeeper OAuth authentication backend"""
    name = 'runkeeper'
    AUTHORIZATION_URL = 'https://runkeeper.com/apps/authorize'
    ACCESS_TOKEN_URL = 'https://runkeeper.com/apps/token'
    ACCESS_TOKEN_METHOD = 'POST'
    EXTRA_DATA = [
        ('userID', 'id'),
    ]

    def get_user_id(self, details, response):
        return response['userID']

    def get_user_details(self, response):
        """Parse username from profile link"""
        username = None
        profile_url = response.get('profile')
        if len(profile_url):
            profile_url_parts = profile_url.split('http://runkeeper.com/user/')
            if len(profile_url_parts) > 1 and len(profile_url_parts[1]):
                username = profile_url_parts[1]
        fullname, first_name, last_name = self.get_user_names(
            fullname=response.get('name')
        )
        return {'username': username,
                'email': response.get('email') or '',
                'fullname': fullname,
                'first_name': first_name,
                'last_name': last_name}

    def user_data(self, access_token, *args, **kwargs):
        # We need to use the /user endpoint to get the user id, the /profile
        # endpoint contains name, user name, location, gender
        user_data = self._user_data(access_token, '/user')
        profile_data = self._user_data(access_token, '/profile')
        return dict(user_data, **profile_data)

    def _user_data(self, access_token, path):
        url = 'https://api.runkeeper.com{0}'.format(path)
        return self.get_json(url, params={'access_token': access_token})
