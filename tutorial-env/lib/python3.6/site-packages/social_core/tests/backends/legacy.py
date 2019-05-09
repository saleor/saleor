import requests

from httpretty import HTTPretty

from ...utils import parse_qs
from .base import BaseBackendTest


class BaseLegacyTest(BaseBackendTest):
    form = ''
    response_body = ''

    def setUp(self):
        super(BaseLegacyTest, self).setUp()
        self.strategy.set_settings({
            'SOCIAL_AUTH_{0}_FORM_URL'.format(self.name):
                self.strategy.build_absolute_uri('/login/{0}'.format(
                    self.backend.name))
        })

    def extra_settings(self):
        return {'SOCIAL_AUTH_{0}_FORM_URL'.format(self.name):
                    '/login/{0}'.format(self.backend.name)}

    def do_start(self):
        start_url = self.strategy.build_absolute_uri(self.backend.start().url)
        HTTPretty.register_uri(
            HTTPretty.GET,
            start_url,
            status=200,
            body=self.form.format(self.complete_url)
        )
        HTTPretty.register_uri(
            HTTPretty.POST,
            self.complete_url,
            status=200,
            body=self.response_body,
            content_type='application/x-www-form-urlencoded'
        )
        response = requests.get(start_url)
        self.assertEqual(response.text, self.form.format(self.complete_url))
        response = requests.post(
            self.complete_url,
            data=parse_qs(self.response_body)
        )
        self.strategy.set_request_data(parse_qs(response.text), self.backend)
        return self.backend.complete()
