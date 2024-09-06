# Should match when logging an exception.
def test_log_info_exception():
    try:
        do_something()
    except Exception as exc:
        # ruleid: exception-object-in-logger-extra
        logger.info("Failed", extra={"error": exc})

# Should match when catching multiple exceptions.
def test_log_catch_multiple_exceptions():
    try:
        do_something()
    except (OSError, FileNotFoundError) as exc:
        # ruleid: exception-object-in-logger-extra
        logger.info("Failed", extra={"error": exc})

# TODO: uncomment once 'except*' is supported by Semgrep
#       https://github.com/semgrep/semgrep/issues/10511
# # Should match when catching an exception group.
# def test_log_catch_wildcard():
#     try:
#         do_something()
#     except* Exception as exc:
#         <add-ruleid-comment-here>: exception-object-in-logger-extra
#         logger.info("Failed", extra={"error": exc})

# Should match when logging an exception in the middle
# of a 'except' block.
def test_log_middle_of_statement():
    try:
        do_something()
    except Exception as exc:
        something()
        # ruleid: exception-object-in-logger-extra
        logger.info("Failed", extra={"error": exc})
        something()

# Should match when catching multiple exceptions.
def test_log_info_exception():
    try:
        do_something()
    except (OSError, FileNotFoundError) as exc:
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

# Should match when using a 'finally' block
def test_log_exception_with_finally_block():
    try:
        do_something()
    except Exception as exc:
        # ruleid: exception-object-in-logger-extra
        logger.info("Failed", extra={"error": exc})
    finally:
        do_something_else()

# Should match when using a 'else' block
def test_log_exception_with_else_block():
    try:
        do_something()
    except Exception as exc:
        # ruleid: exception-object-in-logger-extra
        logger.info("Failed", extra={"error": exc})
    else:
        do_something_else()

# Should match when using a 'finally' and 'else' block
def test_log_exception_with_finally_else_block():
    try:
        do_something()
    except Exception as exc:
        # ruleid: exception-object-in-logger-extra
        logger.info("Failed", extra={"error": exc})
    finally:
        do_something_else()
    else:
        do_something_else()

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

