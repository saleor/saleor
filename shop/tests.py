from unittest import TestSuite, TestLoader

TEST_MODULES = [
    'shop.cart.tests',
    'shop.checkout.tests',
    'shop.communication.tests',
    'shop.core.tests',
    #'shop.delivery.tests',
    'shop.order.tests',
    #'shop.payment.tests',
    #'shop.product.tests',
    'shop.registration.tests',
    'shop.userprofile.tests']

suite = TestSuite()
loader = TestLoader()
for module in TEST_MODULES:
    suite.addTests(loader.loadTestsFromName(module))
