from braintree.attribute_getter import AttributeGetter

class SuccessfulResult(AttributeGetter):
    """
    An instance of this class is returned from most operations when the request is successful.  Call the name of the resource (eg, customer, credit_card, etc) to get the object::

        result = Transaction.sale({..})
        if result.is_success:
            transaction = result.transaction
        else:
            print [error.code for error in result.errors.all]
    """

    @property
    def is_success(self):
        """ Returns whether the result from the gateway is a successful response. """
        return True
