import braintree

class PaginatedCollection(object):
    """
    A class representing results from a paginated list. Supports the iterator protocol::

        results = braintree.MerchantAccount.all()
        for merchant_account in results.items:
            print merchant_account.id
    """

    def __init__(self, method):
        self.__method = method

    @property
    def items(self):
        """ Returns a generator allowing iteration over all of the results. """
        current_page = 0
        total_items = 0
        while True:
            current_page += 1

            results = self.__method(current_page)
            total_items = results.total_items

            for item in results.current_page:
                yield item

            if current_page * results.page_size >= total_items:
                break

    def __iter__(self):
        return self.items
