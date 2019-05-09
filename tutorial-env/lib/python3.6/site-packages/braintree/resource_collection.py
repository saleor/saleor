import braintree
from braintree.exceptions.unexpected_error import UnexpectedError

class ResourceCollection(object):
    """
    A class representing results from a search. Supports the iterator protocol::

        results = braintree.Transaction.search("411111")
        for transaction in results:
            print transaction.id
    """

    def __init__(self, query, results, method):
        if "search_results" not in results:
            raise UnexpectedError("Unprocessable entity due to an invalid request")
        self.__ids = results["search_results"]["ids"]
        self.__method = method
        self.__page_size = results["search_results"]["page_size"]
        self.__query = query

    @property
    def maximum_size(self):
        """
        Returns the approximate size of the results.  The size is approximate due to race conditions when pulling
        back results.  Due to its inexact nature, maximum_size should be avoided.
        """
        return len(self.__ids)

    @property
    def first(self):
        """ Returns the first item in the results. """
        return self.__method(self.__query, self.__ids[0:1])[0]

    @property
    def items(self):
        """ Returns a generator allowing iteration over all of the results. """
        for batch in self.__batch_ids():
            for item in self.__method(self.__query, batch):
                yield item

    @property
    def ids(self):
        """ Returns the list of ids in the search result. """
        return self.__ids

    def __iter__(self):
        return self.items

    def __batch_ids(self):
        for i in range(0, len(self.__ids), self.__page_size):
                yield self.__ids[i:i+self.__page_size]


    @staticmethod
    def _extract_as_array(results, attribute):
        if not attribute in results:
            return []

        value = results[attribute]
        if not isinstance(value, list):
            value = [value]
        return value

