from .oauth import BaseOAuth2


# This provides a backend for python-social-auth. This should not be confused
# with officially battle.net offerings. This piece of code is not officially
# affiliated with Blizzard Entertainment, copyrights to their respective
# owners. See http://us.battle.net/en/forum/topic/13979588015 for more details.


class BattleNetOAuth2(BaseOAuth2):
    """ battle.net Oauth2 backend"""
    name = 'battlenet-oauth2'
    ID_KEY = 'accountId'
    REDIRECT_STATE = False
    AUTHORIZATION_URL = 'https://eu.battle.net/oauth/authorize'
    ACCESS_TOKEN_URL = 'https://eu.battle.net/oauth/token'
    ACCESS_TOKEN_METHOD = 'POST'
    REVOKE_TOKEN_METHOD = 'GET'
    DEFAULT_SCOPE = ['wow.profile']
    EXTRA_DATA = [
        ('refresh_token', 'refresh_token', True),
        ('expires_in', 'expires'),
        ('token_type', 'token_type', True)
    ]

    def get_characters(self, access_token):
        """
        Fetches the character list from the battle.net API. Returns list of
        characters or empty list if the request fails.
        """
        params = {'access_token': access_token}
        if self.setting('API_LOCALE'):
            params['locale'] = self.setting('API_LOCALE')

        response = self.get_json(
            'https://eu.api.battle.net/wow/user/characters',
            params=params
        )
        return response.get('characters') or []

    def get_user_details(self, response):
        """ Return user details from Battle.net account """
        return {'battletag': response.get('battletag')}

    def user_data(self, access_token, *args, **kwargs):
        """ Loads user data from service """
        return self.get_json(
            'https://eu.api.battle.net/account/user',
            params={'access_token': access_token}
        )
