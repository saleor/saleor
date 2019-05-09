from .oauth import BaseOAuth2


class MailChimpOAuth2(BaseOAuth2):
    """MailChimp OAuth2 authentication backend"""
    name = 'mailchimp'
    AUTHORIZATION_URL = 'https://login.mailchimp.com/oauth2/authorize'
    ACCESS_TOKEN_URL = 'https://login.mailchimp.com/oauth2/token'
    METADATA_URL = 'https://login.mailchimp.com/oauth2/metadata'
    ACCESS_TOKEN_METHOD = 'POST'
    STATE_PARAMETER = False
    REDIRECT_STATE = False
    ID_KEY = 'user_id'
    EXTRA_DATA = [
        ('accountname', 'accountname'),
        ('api_endpoint', 'api_endpoint'),
        ('role', 'role'),
        ('login', 'login')
    ]

    def get_user_details(self, response):
        """Return user details from a Mailchimp metadata response"""
        return {
            'username': response['login']['login_name'],
            'email': response['login']['email']
        }

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data and datacenter information from service"""
        return self.get_json(self.METADATA_URL, headers={
          'Authorization': 'OAuth ' + access_token
        })
