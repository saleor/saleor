def test_using_default_token_generator():
    # ruleid: django-no-default-token-generator
    from django.contrib.auth.tokens import default_token_generator


def test_using_token_generator_class():
    # ruleid: django-no-default-token-generator
    from django.contrib.auth.tokens import PasswordResetTokenGenerator

def test_ok_not_using_django_builtin_default_token_generator():
    # ok: django-no-default-token-generator
    from saleor.core.tokens import token_generator

