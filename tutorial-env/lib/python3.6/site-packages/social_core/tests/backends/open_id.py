# -*- coding: utf-8 -*-
import sys

import requests

from six.moves.html_parser import HTMLParser
from openid import oidutil
from httpretty import HTTPretty

sys.path.insert(0, '..')

from .base import BaseBackendTest
from ..strategy import TestStrategy
from ..models import TestStorage, User, TestUserSocialAuth, \
    TestNonce, TestAssociation
from ...utils import parse_qs, module_member
from ...backends.utils import load_backends

# Patch to remove the too-verbose output until a new version is released
oidutil.log = lambda *args, **kwargs: None


class FormHTMLParser(HTMLParser):
    form = {}
    inputs = {}

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'form':
            self.form.update(attrs)
        elif tag == 'input' and 'name' in attrs:
            self.inputs[attrs['name']] = attrs['value']


class OpenIdTest(BaseBackendTest):
    backend_path = None
    backend = None
    access_token_body = None
    user_data_body = None
    user_data_url = ''
    expected_username = ''
    settings = None
    partial_login_settings = None
    raw_complete_url = '/complete/{0}/'

    def setUp(self):
        HTTPretty.enable()
        Backend = module_member(self.backend_path)
        self.strategy = TestStrategy(TestStorage)
        self.complete_url = self.raw_complete_url.format(Backend.name)
        self.backend = Backend(self.strategy, redirect_uri=self.complete_url)
        self.strategy.set_settings({
            'SOCIAL_AUTH_AUTHENTICATION_BACKENDS': (
                self.backend_path,
                'social_core.tests.backends.test_broken.BrokenBackendAuth'
            )
        })
        # Force backends loading to trash PSA cache
        load_backends(
            self.strategy.get_setting('SOCIAL_AUTH_AUTHENTICATION_BACKENDS'),
            force_load=True
        )

    def tearDown(self):
        self.strategy = None
        User.reset_cache()
        TestUserSocialAuth.reset_cache()
        TestNonce.reset_cache()
        TestAssociation.reset_cache()
        HTTPretty.disable()

    def get_form_data(self, html):
        parser = FormHTMLParser()
        parser.feed(html)
        return parser.form, parser.inputs

    def openid_url(self):
        return self.backend.openid_url()

    def post_start(self):
        pass

    def do_start(self):
        HTTPretty.register_uri(HTTPretty.GET,
                               self.openid_url(),
                               status=200,
                               body=self.discovery_body,
                               content_type='application/xrds+xml')
        start = self.backend.start()
        self.post_start()
        form, inputs = self.get_form_data(start)
        HTTPretty.register_uri(HTTPretty.POST,
                               form.get('action'),
                               status=200,
                               body=self.server_response)
        response = requests.post(form.get('action'), data=inputs)
        self.strategy.set_request_data(parse_qs(response.content),
                                       self.backend)
        HTTPretty.register_uri(HTTPretty.POST,
                               form.get('action'),
                               status=200,
                               body='is_valid:true\n')
        return self.backend.complete()
