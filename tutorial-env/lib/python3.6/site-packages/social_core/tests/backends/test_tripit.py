import json

from six.moves.urllib_parse import urlencode

from .oauth import OAuth1Test


class TripitOAuth1Test(OAuth1Test):
    backend_path = 'social_core.backends.tripit.TripItOAuth'
    user_data_url = 'https://api.tripit.com/v1/get/profile'
    expected_username = 'foobar'
    access_token_body = json.dumps({
        'access_token': 'foobar',
        'token_type': 'bearer'
    })
    request_token_body = urlencode({
        'oauth_token_secret': 'foobar-secret',
        'oauth_token': 'foobar',
        'oauth_callback_confirmed': 'true'
    })
    user_data_content_type = 'text/xml'
    user_data_body = \
        '<Response>' \
            '<timestamp>1363590451</timestamp>' \
            '<num_bytes>1040</num_bytes>' \
            '<Profile ref="ignore-me">' \
                '<ProfileEmailAddresses>' \
                    '<ProfileEmailAddress>' \
                        '<address>foobar@gmail.com</address>' \
                        '<is_auto_import>false</is_auto_import>' \
                        '<is_confirmed>true</is_confirmed>' \
                        '<is_primary>true</is_primary>' \
                        '<is_auto_inbox_eligible>' \
                            'true' \
                        '</is_auto_inbox_eligible>' \
                    '</ProfileEmailAddress>' \
                '</ProfileEmailAddresses>' \
                '<is_client>true</is_client>' \
                '<is_pro>false</is_pro>' \
                '<screen_name>foobar</screen_name>' \
                '<public_display_name>Foo Bar</public_display_name>' \
                '<profile_url>people/foobar</profile_url>' \
                '<home_city>Foo, Barland</home_city>' \
                '<activity_feed_url>' \
                    'https://www.tripit.com/feed/activities/private/' \
                    'ignore-this/activities.atom' \
                '</activity_feed_url>' \
                '<alerts_feed_url>' \
                    'https://www.tripit.com/feed/alerts/private/' \
                    'ignore-this/alerts.atom' \
                '</alerts_feed_url>' \
                '<ical_url>' \
                    'webcal://www.tripit.com/feed/ical/private/' \
                    'ignore-this/tripit.ics' \
                '</ical_url>' \
            '</Profile>' \
        '</Response>'

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()


class TripitOAuth1UsernameAlternativesTest(TripitOAuth1Test):
    user_data_body = \
        '<Response>' \
            '<timestamp>1363590451</timestamp>' \
            '<num_bytes>1040</num_bytes>' \
            '<Profile ref="ignore-me">' \
                '<ProfileEmailAddresses>' \
                    '<ProfileEmailAddress>' \
                        '<address>foobar@gmail.com</address>' \
                        '<is_auto_import>false</is_auto_import>' \
                        '<is_confirmed>true</is_confirmed>' \
                        '<is_primary>true</is_primary>' \
                        '<is_auto_inbox_eligible>' \
                            'true' \
                        '</is_auto_inbox_eligible>' \
                    '</ProfileEmailAddress>' \
                '</ProfileEmailAddresses>' \
                '<is_client>true</is_client>' \
                '<is_pro>false</is_pro>' \
                '<screen_name>foobar</screen_name>' \
                '<public_display_name>Foobar</public_display_name>' \
                '<profile_url>people/foobar</profile_url>' \
                '<home_city>Foo, Barland</home_city>' \
                '<activity_feed_url>' \
                    'https://www.tripit.com/feed/activities/private/' \
                    'ignore-this/activities.atom' \
                '</activity_feed_url>' \
                '<alerts_feed_url>' \
                    'https://www.tripit.com/feed/alerts/private/' \
                    'ignore-this/alerts.atom' \
                '</alerts_feed_url>' \
                '<ical_url>' \
                    'webcal://www.tripit.com/feed/ical/private/' \
                    'ignore-this/tripit.ics' \
                '</ical_url>' \
            '</Profile>' \
        '</Response>'
