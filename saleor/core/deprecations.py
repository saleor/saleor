class SaleorDeprecationWarning(UserWarning):
    """Custom deprecation warning as DeprecationWarning is usually ignored.

    Learn more: https://sethmlarson.dev/deprecations-via-warnings-dont-work-for-python-libraries
    """
