from unittest import TestCase

from django.template.response import TemplateResponse
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
        assert step.forms_are_valid()

    def test_process(self):
        request = MagicMock()
        request.method = 'GET'
        step = SimpleStep(request)
        assert isinstance(step.process(), TemplateResponse)
        request.method = 'POST'
        assert step.process() is None
