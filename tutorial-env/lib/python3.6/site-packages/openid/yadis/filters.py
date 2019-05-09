"""This module contains functions and classes used for extracting
endpoint information out of a Yadis XRD file using the ElementTree XML
parser.
"""

__all__ = [
    'BasicServiceEndpoint',
    'mkFilter',
    'IFilter',
    'TransformFilterMaker',
    'CompoundFilter',
]

from openid.yadis.etxrd import expandService
import collections


class BasicServiceEndpoint(object):
    """Generic endpoint object that contains parsed service
    information, as well as a reference to the service element from
    which it was generated. If there is more than one xrd:Type or
    xrd:URI in the xrd:Service, this object represents just one of
    those pairs.

    This object can be used as a filter, because it implements
    fromBasicServiceEndpoint.

    The simplest kind of filter you can write implements
    fromBasicServiceEndpoint, which takes one of these objects.
    """

    def __init__(self, yadis_url, type_uris, uri, service_element):
        self.type_uris = type_uris
        self.yadis_url = yadis_url
        self.uri = uri
        self.service_element = service_element

    def matchTypes(self, type_uris):
        """Query this endpoint to see if it has any of the given type
        URIs. This is useful for implementing other endpoint classes
        that e.g. need to check for the presence of multiple versions
        of a single protocol.

        @param type_uris: The URIs that you wish to check
        @type type_uris: iterable of str

        @return: all types that are in both in type_uris and
            self.type_uris
        """
        return [uri for uri in type_uris if uri in self.type_uris]

    def fromBasicServiceEndpoint(endpoint):
        """Trivial transform from a basic endpoint to itself. This
        method exists to allow BasicServiceEndpoint to be used as a
        filter.

        If you are subclassing this object, re-implement this function.

        @param endpoint: An instance of BasicServiceEndpoint
        @return: The object that was passed in, with no processing.
        """
        return endpoint

    fromBasicServiceEndpoint = staticmethod(fromBasicServiceEndpoint)


class IFilter(object):
    """Interface for Yadis filter objects. Other filter-like things
    are convertable to this class."""

    def getServiceEndpoints(self, yadis_url, service_element):
        """Returns an iterator of endpoint objects"""
        raise NotImplementedError


class TransformFilterMaker(object):
    """Take a list of basic filters and makes a filter that transforms
    the basic filter into a top-level filter. This is mostly useful
    for the implementation of mkFilter, which should only be needed
    for special cases or internal use by this library.

    This object is useful for creating simple filters for services
    that use one URI and are specified by one Type (we expect most
    Types will fit this paradigm).

    Creates a BasicServiceEndpoint object and apply the filter
    functions to it until one of them returns a value.
    """

    def __init__(self, filter_functions):
        """Initialize the filter maker's state

        @param filter_functions: The endpoint transformer functions to
            apply to the basic endpoint. These are called in turn
            until one of them does not return None, and the result of
            that transformer is returned.
        """
        self.filter_functions = filter_functions

    def getServiceEndpoints(self, yadis_url, service_element):
        """Returns an iterator of endpoint objects produced by the
        filter functions."""
        endpoints = []

        # Do an expansion of the service element by xrd:Type and xrd:URI
        for type_uris, uri, _ in expandService(service_element):

            # Create a basic endpoint object to represent this
            # yadis_url, Service, Type, URI combination
            endpoint = BasicServiceEndpoint(yadis_url, type_uris, uri,
                                            service_element)

            e = self.applyFilters(endpoint)
            if e is not None:
                endpoints.append(e)

        return endpoints

    def applyFilters(self, endpoint):
        """Apply filter functions to an endpoint until one of them
        returns non-None."""
        for filter_function in self.filter_functions:
            e = filter_function(endpoint)
            if e is not None:
                # Once one of the filters has returned an
                # endpoint, do not apply any more.
                return e

        return None


class CompoundFilter(object):
    """Create a new filter that applies a set of filters to an endpoint
    and collects their results.
    """

    def __init__(self, subfilters):
        self.subfilters = subfilters

    def getServiceEndpoints(self, yadis_url, service_element):
        """Generate all endpoint objects for all of the subfilters of
        this filter and return their concatenation."""
        endpoints = []
        for subfilter in self.subfilters:
            endpoints.extend(
                subfilter.getServiceEndpoints(yadis_url, service_element))
        return endpoints


# Exception raised when something is not able to be turned into a filter
filter_type_error = TypeError(
    'Expected a filter, an endpoint, a callable or a list of any of these.')


def mkFilter(parts):
    """Convert a filter-convertable thing into a filter

    @param parts: a filter, an endpoint, a callable, or a list of any of these.
    """
    # Convert the parts into a list, and pass to mkCompoundFilter
    if parts is None:
        parts = [BasicServiceEndpoint]

    try:
        parts = list(parts)
    except TypeError:
        return mkCompoundFilter([parts])
    else:
        return mkCompoundFilter(parts)


def mkCompoundFilter(parts):
    """Create a filter out of a list of filter-like things

    Used by mkFilter

    @param parts: list of filter, endpoint, callable or list of any of these
    """
    # Separate into a list of callables and a list of filter objects
    transformers = []
    filters = []
    for subfilter in parts:
        try:
            subfilter = list(subfilter)
        except TypeError:
            # If it's not an iterable
            if hasattr(subfilter, 'getServiceEndpoints'):
                # It's a full filter
                filters.append(subfilter)
            elif hasattr(subfilter, 'fromBasicServiceEndpoint'):
                # It's an endpoint object, so put its endpoint
                # conversion attribute into the list of endpoint
                # transformers
                transformers.append(subfilter.fromBasicServiceEndpoint)
            elif isinstance(subfilter, collections.Callable):
                # It's a simple callable, so add it to the list of
                # endpoint transformers
                transformers.append(subfilter)
            else:
                raise filter_type_error
        else:
            filters.append(mkCompoundFilter(subfilter))

    if transformers:
        filters.append(TransformFilterMaker(transformers))

    if len(filters) == 1:
        return filters[0]
    else:
        return CompoundFilter(filters)
