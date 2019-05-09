def generate_test_payment_method_code(number):
    return "stub-" + number

VisaPaymentMethodCode = generate_test_payment_method_code("4111111111111111")
InvalidPaymentMethodCode = generate_test_payment_method_code("invalid-payment-method-code")

Session = "stub-session"
InvalidSession = "stub-invalid-session"
