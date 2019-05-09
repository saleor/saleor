import json

from .oauth import OAuth2Test


class MapMyFitnessOAuth2Test(OAuth2Test):
    backend_path = 'social_core.backends.mapmyfitness.MapMyFitnessOAuth2'
    user_data_url = 'https://oauth2-api.mapmyapi.com/v7.0/user/self/'
    expected_username = 'FredFlinstone'
    access_token_body = json.dumps({
        'access_token': 'foobar',
        'token_type': 'Bearer',
        'expires_in': 4000000,
        'refresh_token': 'bambaz',
        'scope': 'read'
    })
    user_data_body = json.dumps({
        'last_name': 'Flinstone',
        'weight': 91.17206637,
        'communication': {
            'promotions': True,
            'newsletter': True,
            'system_messages': True
        },
        'height': 1.778,
        'token_type': 'Bearer',
        'id': 112233,
        'date_joined': '2011-08-26T06:06:19+00:00',
        'first_name': 'Fred',
        'display_name': 'Fred Flinstone',
        'display_measurement_system': 'imperial',
        'expires_in': 4000000,
        '_links': {
            'stats': [
                {
                    'href': '/v7.0/user_stats/112233/?'
                            'aggregate_by_period=month',
                    'id': '112233',
                    'name': 'month'
                },
                {
                    'href': '/v7.0/user_stats/112233/?'
                            'aggregate_by_period=year',
                    'id': '112233',
                    'name': 'year'
                },
                {
                    'href': '/v7.0/user_stats/112233/?aggregate_by_period=day',
                    'id': '112233',
                    'name': 'day'
                },
                {
                    'href': '/v7.0/user_stats/112233/?'
                            'aggregate_by_period=week',
                    'id': '112233',
                    'name': 'week'
                },
                {
                    'href': '/v7.0/user_stats/112233/?'
                            'aggregate_by_period=lifetime',
                    'id': '112233',
                    'name': 'lifetime'
                }
            ],
            'friendships': [
                {
                    'href': '/v7.0/friendship/?from_user=112233'
                }
            ],
            'privacy': [
                {
                    'href': '/v7.0/privacy_option/3/',
                    'id': '3',
                    'name': 'profile'
                },
                {
                    'href': '/v7.0/privacy_option/3/',
                    'id': '3',
                    'name': 'workout'
                },
                {
                    'href': '/v7.0/privacy_option/3/',
                    'id': '3',
                    'name': 'activity_feed'
                },
                {
                    'href': '/v7.0/privacy_option/1/',
                    'id': '1',
                    'name': 'food_log'
                },
                {
                    'href': '/v7.0/privacy_option/3/',
                    'id': '3',
                    'name': 'email_search'
                },
                {
                    'href': '/v7.0/privacy_option/3/',
                    'id': '3',
                    'name': 'route'
                }
            ],
            'image': [
                {
                    'href': '/v7.0/user_profile_photo/112233/',
                    'id': '112233',
                    'name': 'user_profile_photo'
                }
            ],
            'documentation': [
                {
                    'href': 'https://www.mapmyapi.com/docs/User'
                }
            ],
            'workouts': [
                {
                    'href': '/v7.0/workout/?user=112233&'
                            'order_by=-start_datetime'
                }
            ],
            'deactivation': [
                {
                    'href': '/v7.0/user_deactivation/'
                }
            ],
            'self': [
                {
                    'href': '/v7.0/user/112233/',
                    'id': '112233'
                }
            ]
        },
        'location': {
            'country': 'US',
            'region': 'NC',
            'locality': 'Bedrock',
            'address': '150 Dinosaur Ln'
        },
        'last_login': '2014-02-23T22:36:52+00:00',
        'email': 'fredflinstone@gmail.com',
        'username': 'FredFlinstone',
        'sharing': {
            'twitter': False,
            'facebook': False
        },
        'scope': 'read',
        'refresh_token': 'bambaz',
        'last_initial': 'S.',
        'access_token': 'foobar',
        'gender': 'M',
        'time_zone': 'America/Denver',
        'birthdate': '1983-04-15'
    })

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()
