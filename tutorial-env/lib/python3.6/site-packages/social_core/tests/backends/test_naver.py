import json

from .oauth import OAuth2Test


class NaverOAuth2Test(OAuth2Test):
    backend_path = 'social_core.backends.naver.NaverOAuth2'
    user_data_url = 'https://openapi.naver.com/v1/nid/getUserProfile.xml'
    expected_username = 'foobar'
    access_token_body = json.dumps({
        'access_token': 'foobar',
        'token_type': 'bearer',
    })

    user_data_content_type = 'text/xml'
    user_data_body = \
    '<?xml version="1.0" encoding="UTF-8" ?>' \
    '<data>' \
        '<result>' \
            '<resultcode>00</resultcode>' \
            '<message>success</message>' \
        '</result>' \
        '<response>' \
            '<email><![CDATA[foobar@naver.com]]></email>' \
            '<nickname><![CDATA[foobar]]></nickname>' \
            '<profile_image>' \
                '<![CDATA[http://naver.com/image.url.jpg]]>' \
            '</profile_image>' \
            '<age><![CDATA[20-29]]></age>' \
            '<gender>M</gender>' \
            '<id><![CDATA[123456]]></id>' \
            '<name><![CDATA[foobar]]></name>' \
            '<birthday><![CDATA[12-01]]></birthday>' \
        '</response>' \
    '</data>'

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()
