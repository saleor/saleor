import gc

import pytest
from authlib.integrations.requests_client import OAuth2Session

from .utils import (
    clean_up_after_garbage_collection_test,
    disable_gc_for_garbage_collection_test,
)


# Group all tests that require garbage collection so that they do not run concurrently.
# This is necessary to ensure that tests don't interfere with each other.
# Without grouping we could receive false positive results.
@pytest.mark.xdist_group(name="garbage_collection")
def test_OAuth2Session_remove_all_reference_cycles():
    try:
        # given
        # Disable automatic garbage collection and set debugging flag.
        disable_gc_for_garbage_collection_test()

        # when
        # Create 0Auth2Session object
        OAuth2Session()
        # Enforce garbage collection to populate the garbage list for inspection.
        gc.collect()

        # then
        # Ensure that the garbage list is empty. The garbage list is only valid
        # until the next collection cycle so we can only make assertions about it
        # before re-enabling automatic collection.
        assert gc.garbage == []
    # Restore garbage collection settings to their original state. This should always be run to avoid interfering
    # with other tests to ensure that code should be executed in the `finally' block.
    finally:
        clean_up_after_garbage_collection_test()
