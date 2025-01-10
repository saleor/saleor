import warnings

from django.core.cache import CacheKeyWarning, cache


def test_ignore_cache_key_warning():
    key_over_250_characters = 300 * "x"

    # Ensure all warnings are errors
    warnings.simplefilter("error")

    # Ignore CacheKeyWarning
    warnings.filterwarnings("ignore", category=CacheKeyWarning)

    # Call a function that throws warning
    cache.set(key_over_250_characters, "bar")
