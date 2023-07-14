from ...checkout.models import Checkout
from ...checkout.utils import get_or_create_checkout_metadata


# `instance = get_checkout_metadata(instance)` is calling the
# `get_checkout_metadata` function to retrieve the metadata associated with a
# checkout instance. This function is defined in the `.../checkout/utils.py` file
# and takes a `Checkout` instance as an argument. It returns a dictionary
# containing the metadata associated with the checkout.
def get_valid_metadata_instance(instance):
    if isinstance(instance, Checkout):
        instance = get_or_create_checkout_metadata(instance)
    return instance
