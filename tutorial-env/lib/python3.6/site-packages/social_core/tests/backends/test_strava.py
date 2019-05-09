import json

from .oauth import OAuth2Test


class StravaOAuthTest(OAuth2Test):
    backend_path = 'social_core.backends.strava.StravaOAuth'
    user_data_url = 'https://www.strava.com/api/v3/athlete'
    expected_username = '227615'
    access_token_body = json.dumps({
      "access_token": "83ebeabdec09f6670863766f792ead24d61fe3f9",
      "athlete": {
        "id": 227615,
        "resource_state": 3,
        "firstname": "John",
        "lastname": "Applestrava",
        "profile_medium": "http://pics.com/227615/medium.jpg",
        "profile": "http://pics.com/227615/large.jpg",
        "city": "San Francisco",
        "state": "California",
        "country": "United States",
        "sex": "M",
        "friend": "null",
        "follower": "null",
        "premium": "true",
        "created_at": "2008-01-01T17:44:00Z",
        "updated_at": "2013-09-04T20:00:50Z",
        "follower_count": 273,
        "friend_count": 19,
        "mutual_friend_count": 0,
        "date_preference": "%m/%d/%Y",
        "measurement_preference": "feet",
        "email": "john@applestrava.com",
        "clubs": [],
        "bikes": [],
        "shoes": []
      }
    })
    user_data_body = json.dumps({
      "id": 227615,
      "resource_state": 2,
      "firstname": "John",
      "lastname": "Applestrava",
      "profile_medium": "http://pics.com/227615/medium.jpg",
      "profile": "http://pics.com/227615/large.jpg",
      "city": "San Francisco",
      "state": "CA",
      "country": "United States",
      "sex": "M",
      "friend": "null",
      "follower": "accepted",
      "premium": "true",
      "created_at": "2011-03-19T21:59:57Z",
      "updated_at": "2013-09-05T16:46:54Z",
      "approve_followers": "false"
    })

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()
