# Should match when logging an exception.
def test_log_info_exception():
    try:
        do_something()
    except Exception as exc:
        # ruleid: exception-object-in-logger-extra
        logger.info("Failed", extra={"error": exc})

# Should match when extra contains multiple keys & values.
def test_log_multiple_extra():
    try:
        do_something()
    except Exception as exc:
        # ruleid: exception-object-in-logger-extra
        logger.info("Failed", extra={"other1": 1, "error": exc, "other2": 1})

# Should match when extra is before other arguments (case #1).
def test_log_exception_trailing_arguments_case1():
    try:
        do_something()
    except Exception as exc:
        # w/ exc_info trailing & extra={} in the middle
        # ruleid: exception-object-in-logger-extra
        logger.info("Failed", extra={"error": exc}, exc_info=True)


# Should match when extra is before other arguments (case #2).
def test_log_exception_trailing_arguments_case2():
    try:
        do_something()
    except Exception as exc:
        # Test: extra={} is first parameter
        # ruleid: exception-object-in-logger-extra
        logger.info(extra={"error": exc}, msg="Failed", exc_info=True)

# Should not match when converting an exception object to string.
def test_not_logging_exception():
    try:
        do_something()
    except Exception as exc:
        # ok: exception-object-in-logger-extra
        logger.info("Failed", extra={"exc": str(exc)})


# Should not match when using an attribute from the exception object.
def test_not_logging_exception():
    try:
        do_something()
    except Exception as exc:
        # ok: exception-object-in-logger-extra
        logger.info("Failed", extra={"exc": exc.message})

