import jwt

from social_core.backends.oauth import BaseOAuth2


class KeycloakOAuth2(BaseOAuth2):  # pylint: disable=abstract-method
    """Keycloak OAuth2 authentication backend

    This backend has been tested working with a standard Keycloak installation,
    but you might have to specialize it and tune the parameters per your configuration.

    This setup specializes the OAuth2 backend which, strictly speaking,
    offers authorization without authentication capabilities.

    Keycloak does offer a full OpenID Connect implementation,
    but the implementation is rather labor intensive to implement.

    This backend is configured to get an access token instead, and assume that the
    access token contains the necessary user details for authentication.

    The integrity of the authentication process is followed by public key verification
    for the `access_token` along with OpenID Connect specification `aud` field checking.

    To set up, please take the following steps:

    1. Create a new Keycloak client in the Clients section.

    2. Configure the following parameters in the Client setup:

        Settings > Client ID (copy to settings as `KEY` value)
        Credentials > Client Authenticator > Secret (copy to settings as `SECRET` value)

    3. For the tokens to work with the JWT setup the following configuration has to be made in Keycloak:

        Settings > Access Type > confidential
        Settings > Fine Grain OpenID Connect Configuration > User Info Signed Response Algorithm > RS256
        Settings > Fine Grain OpenID Connect Configuration > Request Object Signature Algorithm > RS256

    4. Get the public key (copy to settings as `PUBLIC_KEY` value) to be used with the backend:

        Realm Settings > Keys > Public key

    5. Configure access token fields are configured via the Keycloak Client mappers:

        Clients > Client ID > Mappers

    They have to include at least the `ID_KEY` value and the dictionary keys defined in the `get_user_details` method.

    6. Configure your web backend. Example setting values for Django settings could be:

        SOCIAL_AUTH_KEYCLOAK_KEY = 'example'
        SOCIAL_AUTH_KEYCLOAK_SECRET = '1234abcd-1234-abcd-1234-abcd1234adcd'
        SOCIAL_AUTH_KEYCLOAK_PUBLIC_KEY = 'pempublickeythatis2048bitsinbase64andhaseg392characters'
        SOCIAL_AUTH_KEYCLOAK_AUTHORIZATION_URL = 'https://sso.example.com/auth/realms/example/protocol/openid-connect/auth'
        SOCIAL_AUTH_KEYCLOAK_ACCESS_TOKEN_URL = 'https://sso.example.com/auth/realms/example/protocol/openid-connect/token'

    7. The default behaviour is to associate users via username field, but you can change the key with e.g.

            SOCIAL_AUTH_KEYCLOAK_ID_KEY = 'email'

    Please make sure your Keycloak user database and Django user database do not conflict
    and that there is no risk of user account hijacking by false account association.
    """

    name = 'keycloak'
    ID_KEY = 'username'
    ACCESS_TOKEN_METHOD = 'POST'

    def authorization_url(self):
        return self.setting('AUTHORIZATION_URL')

    def access_token_url(self):
        return self.setting('ACCESS_TOKEN_URL')

    def audience(self):
        return self.setting('KEY')

    def algorithm(self):
        return self.setting('ALGORITHM', default='RS256')

    def public_key(self):
        return '\n'.join([
            '-----BEGIN PUBLIC KEY-----',
            self.setting('PUBLIC_KEY'),
            '-----END PUBLIC KEY-----',
        ])

    def user_data(self, access_token, *args, **kwargs):  # pylint: disable=unused-argument
        """Decode user data from the access_token

        You can specialize this method to e.g. get information
        from the Keycloak backend if you do not want to include
        the user information in the access_token.
        """

        return jwt.decode(
            access_token,
            key=self.public_key(),
            algorithms=self.algorithm(),
            audience=self.audience(),
        )

    def get_user_details(self, response):
        """Map fields in user_data into Django User fields
        """

        return {
            'username': response.get('preferred_username'),
            'email': response.get('email'),
            'fullname': response.get('name'),
            'first_name': response.get('given_name'),
            'last_name': response.get('family_name'),
        }

    def get_user_id(self, details, response):
        """Get and associate Django User by the field indicated by ID_KEY
        """

        return details.get(self.ID_KEY)
