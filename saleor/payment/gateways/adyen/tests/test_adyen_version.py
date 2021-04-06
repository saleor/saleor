from Adyen.settings import API_CHECKOUT_VERSION, API_PAYMENT_VERSION


def test_adyen_api_version_not_changed():
    # We shouldn't bump the Adyen API version when we make a path release.
    # We could bump Adyen API when we make a major or minor release.
    # If we bump Adyen API we should provide it as breaking changes because
    # Saleor clients may require to update part of their code (e.g. in mobile devices).
    assert API_CHECKOUT_VERSION == "v64"
    assert API_PAYMENT_VERSION == "v64"
