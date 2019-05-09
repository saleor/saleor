from braintree.attribute_getter import AttributeGetter

class ValidationError(AttributeGetter):
    """
    A validation error returned from the server, with information about the error:

    * **attribute**: The field which had an error.
    * **code**: A numeric error code. See :class:`ErrorCodes <braintree.error_codes.ErrorCodes>`
    * **message**: A description of the error.  Note: error messages may change, but the code will not.
    """
    pass
