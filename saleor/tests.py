from unittest import TestSuite, TestLoader

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
    'saleor.userprofile.tests',
    'saleor.currency_converter.tests'
]

suite = TestSuite()
loader = TestLoader()
for module in TEST_MODULES:
    suite.addTests(loader.loadTestsFromName(module))
