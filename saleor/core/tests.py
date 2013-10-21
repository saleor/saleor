from django.template.response import TemplateResponse
from django.test import TestCase
from mock import MagicMock
from satchless.process import InvalidData

from .utils import BaseStep


class SimpleStep(BaseStep):

    def __str__(self):
        return 'simple'

    def save(self):
        pass

    def validate(self):
        raise InvalidData()

    def get_absolute_url(self):
        return '/'


class SimpleStepTest(TestCase):

    def test_forms_are_valid(self):
        request = MagicMock()
        request.method = 'GET'
        step = SimpleStep(request)
        self.assert_(step.forms_are_valid())

    def test_process(self):
        request = MagicMock()
        request.method = 'GET'
        step = SimpleStep(request)
        self.assertEqual(type(step.process()), TemplateResponse)
        request.method = 'POST'
        self.assertEqual(step.process(), None)
