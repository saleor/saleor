import braintree
from braintree.configuration import Configuration

class TransparentRedirect:
    """
    A class used for Transparent Redirect operations
    """

    class Kind(object):
        CreateCustomer = "create_customer"
        UpdateCustomer = "update_customer"
        CreatePaymentMethod = "create_payment_method"
        UpdatePaymentMethod = "update_payment_method"
        CreateTransaction = "create_transaction"

    @staticmethod
    def confirm(query_string):
        """
        Confirms a transparent redirect request. It expects the query string from the
        redirect request. The query string should _not_ include the leading "?" character. ::

            result = braintree.TransparentRedirect.confirm("foo=bar&id=12345")
        """
        return Configuration.gateway().transparent_redirect.confirm(query_string)


    @staticmethod
    def tr_data(data, redirect_url):
        return Configuration.gateway().transparent_redirect.tr_data(data, redirect_url)

    @staticmethod
    def url():
        """
        Returns the url for POSTing Transparent Redirect HTML forms
        """
        return Configuration.gateway().transparent_redirect.url()

