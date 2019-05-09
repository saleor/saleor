import json
from .oauth import OAuth2Test


class ArcGISOAuth2Test(OAuth2Test):
    user_data_url = 'https://www.arcgis.com/sharing/rest/community/self'
    backend_path = 'social_core.backends.arcgis.ArcGISOAuth2'
    expected_username = 'gis@rocks.com'

    user_data_body = json.dumps({
        'first_name': 'Gis',
        'last_name': 'Rocks',
        'email': 'gis@rocks.com',
        'fullName': 'Gis Rocks',
        'username': 'gis@rocks.com'
    })

    access_token_body = json.dumps({
        'access_token': 'CM-gcB85taGhRmoI7l3PSGaXUNsaLkTg-dHH7XtA9Dnlin' \
                        'PYKBBrIvFzhd1JtDhh7hEwSv_6eLLcLtUqe3gD6i1yaYYF' \
                        'pUQJwy8KEujke5AE87tP9XIoMtp4_l320pUL',
        'expires_in': 86400
    })

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()
