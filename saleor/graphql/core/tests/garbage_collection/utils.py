import gc


def disable_gc_for_garbage_collection_test():
    # Disable automatic garbage collection. To have control over when
    # garbage collection is performed. This is necessary to ensure that another
    # that thread doesn't accidentally trigger it by simply executing code.
    gc.disable()

    # Delete the garbage list(`gc.garbage`) to ensure that other tests don't
    # interfere with this test.
    gc.collect()

    # Set the garbage collection debugging flag to store all unreachable
    # objects in `gc.garbage`. This is necessary to ensure that the
    # garbage list is empty after execute test code. Otherwise, the test
    # will always pass. The garbage list isn't automatically populated
    # because it costs extra CPU cycles
    gc.set_debug(gc.DEBUG_SAVEALL)


def clean_up_after_garbage_collection_test():
    # Clean up the garbage collection settings. Re-enable automatic garbage
    # collection. This step is mandatory to avoid running other tests without
    # automatic garbage collection.
    gc.set_debug(0)
    gc.enable()
