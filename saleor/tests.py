from unittest import TestSuite, TestLoader

import django

if hasattr(django, 'setup'):
    django.setup()


TEST_MODULES = [
    'saleor.cart.tests',
    'saleor.checkout.tests',
    'saleor.communication.tests',
    'saleor.core.tests',
    #'saleor.delivery.tests',
    'saleor.order.tests',
    #'saleor.payment.tests',
    #'saleor.product.tests',
    'saleor.registration.tests',
    'saleor.userprofile.tests']

suite = TestSuite()
loader = TestLoader()
for module in TEST_MODULES:
    suite.addTests(loader.loadTestsFromName(module))
