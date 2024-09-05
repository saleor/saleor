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

