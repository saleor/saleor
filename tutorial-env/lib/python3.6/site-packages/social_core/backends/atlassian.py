from social_core.backends.oauth import BaseOAuth2


class AtlassianOAuth2(BaseOAuth2):
    name = 'atlassian'
    AUTHORIZATION_URL = 'https://accounts.atlassian.com/authorize'
    ACCESS_TOKEN_METHOD = 'POST'
    ACCESS_TOKEN_URL = 'https://api.atlassian.com/oauth/token'
    DEFAULT_SCOPE = ['read:jira-user', 'offline_access']
    ID_KEY = 'accountId'
    EXTRA_DATA = [
        ('resources', 'resources'),
        ('refresh_token', 'refresh_token'),
        ('expires_in', 'expires_in'),
    ]

    def auth_params(self, state=None):
        params = super(AtlassianOAuth2, self).auth_params(state)
        params.update({'audience': 'api.atlassian.com',
                       'prompt': 'consent'})
        return params

    def get_user_details(self, response):
        fullname, first_name, last_name = self.get_user_names(response['displayName'])
        return {'username': response['name'],
                'email': response['emailAddress'],
                'fullname': fullname,
                'first_name': first_name,
                'last_name': last_name}

    def user_data(self, access_token, *args, **kwargs):
        resources = self.get_json('https://api.atlassian.com/oauth/token/accessible-resources',
                                  headers={'Authorization': 'Bearer {}'.format(access_token)})
        user_info = self.get_json('https://api.atlassian.com/ex/jira/{}/rest/api/2/myself'.format(resources[0]['id']),
                                  headers={'Authorization': 'Bearer {}'.format(access_token)})
        user_info['resources'] = resources
        return user_info
