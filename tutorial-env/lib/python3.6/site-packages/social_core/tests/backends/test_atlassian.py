import json

from httpretty import HTTPretty

from .oauth import OAuth2Test


class AtlassianOAuth2Test(OAuth2Test):
    backend_path = 'social_core.backends.atlassian.AtlassianOAuth2'
    tenant_url = 'https://api.atlassian.com/oauth/token/accessible-resources'
    user_data_url = 'https://api.atlassian.com/ex/jira/FAKED_CLOUD_ID/rest/api/2/myself'
    expected_username = 'erlich'
    access_token_body = json.dumps({
        'access_token': 'aviato',
        'token_type': 'bearer'
    })
    tenant_data_body = json.dumps([
      {
          "id": "FAKED_CLOUD_ID",
          "name": "bachmanity.com",
          "avatarUrl": "https://bachmanity.atlassian.net/avatars/240/site.png",
          "scopes": [
            "read:jira-user"
          ]
      }
    ])
    user_data_body = json.dumps({
        "self": "http://bachmanity.atlassian.net/rest/api/3/user?username=erlich",
        "key": "erlich",
        "accountId": "99:27935d01-92a7-4687-8272-a9b8d3b2ae2e",
        "name": "erlich",
        "emailAddress": "erlich@bachmanity.com",
        "avatarUrls": {
            "48x48": "http://bachmanity.atlassian.net/secure/useravatar?size=large&ownerId=erlich",
            "24x24": "http://bachmanity.atlassian.net/secure/useravatar?size=small&ownerId=erlich",
            "16x16": "http://bachmanity.atlassian.net/secure/useravatar?size=xsmall&ownerId=erlich",
            "32x32": "http://bachmanity.atlassian.net/secure/useravatar?size=medium&ownerId=erlich"
        },
        "displayName": "Erlich Bachman",
        "active": True,
        "timeZone": "Australia/Sydney",
        "groups": {
            "size": 3,
            "items": []
        },
        "applicationRoles": {
            "size": 1,
            "items": []
        }
    })

    def auth_handlers(self, start_url):
        target_url = super(AtlassianOAuth2Test, self).auth_handlers(start_url)
        HTTPretty.register_uri(HTTPretty.GET,
                               self.tenant_url,
                               body=self.tenant_data_body,
                               content_type='application/json')
        return target_url

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()
