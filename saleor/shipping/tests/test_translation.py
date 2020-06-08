import pytest

from ..models import ShippingMethodTranslation


@pytest.fixture
def shipping_method_translation_fr(shipping_method):
    return ShippingMethodTranslation.objects.create(
        language_code="fr", shipping_method=shipping_method, name="French name"
    )


def shipping_method_translation(
    settings, shipping_method, shipping_method_translation_fr
):
    assert not shipping_method.translated.name == "French name"
    settings.LANGUAGE_CODE = "fr"
    assert shipping_method.translated.name == "French name"
