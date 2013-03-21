from .. import Step
from ..models import Order
from .steps import (TestBaseShippingStep, TestBillingAddressStep,
                    TestShippingStep)
from django.core.urlresolvers import reverse
from django.template.response import TemplateResponse
from django.test import TestCase
from mock import MagicMock
from satchless.process import InvalidData


class SimpleStep(Step):

    def __str__(self):
        return 'simple'

    def save(self):
        pass

    def validate(self):
        raise InvalidData()


class SimpleStepTest(TestCase):

    def setUp(self):
        self.order = Order.objects.create()
        self.request = MagicMock()
        self.request.method = 'GET'

    def test_get_absolute_url(self):
        step = SimpleStep(self.order, self.request)
        url = reverse('order:details', kwargs={'token': self.order.token,
                                               'step':str(step)})
        self.assertEqual(step.get_absolute_url(), url)

    def test_forms_are_valid(self):
        step = SimpleStep(self.order, self.request)
        self.assert_(step.forms_are_valid())

    def test_process(self):
        step = SimpleStep(self.order, self.request)
        self.assertEqual(type(step.process()), TemplateResponse)
        self.request.method = 'POST'
        self.assertEqual(step.process(), None)
