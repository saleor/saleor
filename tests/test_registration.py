from django.contrib.auth import get_user_model

User = get_user_model()


def test_base_backend(authorization_key, base_backend):
    assert authorization_key.site_settings.site.domain == "mirumee.com"
    key, secret = base_backend.get_key_and_secret()
    assert key == "Key"
    assert secret == "Password"


def test_backend_no_site(settings, authorization_key, base_backend):
    settings.SITE_ID = None
    assert base_backend.get_key_and_secret() is None
