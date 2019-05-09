# -*- test-case-name: yadis.test.test_etxrd -*-
"""
ElementTree interface to an XRD document.
"""

__all__ = [
    'nsTag',
    'mkXRDTag',
    'isXRDS',
    'parseXRDS',
    'getCanonicalID',
    'getYadisXRD',
    'getPriorityStrict',
    'getPriority',
    'prioSort',
    'iterServices',
    'expandService',
    'expandServices',
]

import sys
import random
import functools

from datetime import datetime
from time import strptime

from openid.oidutil import importElementTree, importSafeElementTree

ElementTree = importElementTree()
SafeElementTree = importSafeElementTree()

from openid.yadis import xri


class XRDSError(Exception):
    """An error with the XRDS document."""

    # The exception that triggered this exception
    reason = None


class XRDSFraud(XRDSError):
    """Raised when there's an assertion in the XRDS that it does not have
    the authority to make.
    """


def parseXRDS(text):
    """Parse the given text as an XRDS document.

    @return: ElementTree containing an XRDS document

    @raises XRDSError: When there is a parse error or the document does
        not contain an XRDS.
    """
    try:
        # lxml prefers to parse bytestrings, and occasionally chokes on a
        # combination of text strings and declared XML encodings -- see
        # https://github.com/necaris/python3-openid/issues/19
        # To avoid this, we ensure that the 'text' we're parsing is actually
        # a bytestring
        bytestring = text.encode('utf8') if isinstance(text, str) else text
        element = SafeElementTree.XML(bytestring)
    except (SystemExit, MemoryError, AssertionError, ImportError):
        raise
    except Exception as why:
        exc = XRDSError('Error parsing document as XML')
        exc.reason = why
        raise exc
    else:
        tree = ElementTree.ElementTree(element)
        if not isXRDS(tree):
            raise XRDSError('Not an XRDS document')

        return tree


XRD_NS_2_0 = 'xri://$xrd*($v*2.0)'
XRDS_NS = 'xri://$xrds'


def nsTag(ns, t):
    return '{%s}%s' % (ns, t)


def mkXRDTag(t):
    """basestring -> basestring

    Create a tag name in the XRD 2.0 XML namespace suitable for using
    with ElementTree
    """
    return nsTag(XRD_NS_2_0, t)


def mkXRDSTag(t):
    """basestring -> basestring

    Create a tag name in the XRDS XML namespace suitable for using
    with ElementTree
    """
    return nsTag(XRDS_NS, t)


# Tags that are used in Yadis documents
root_tag = mkXRDSTag('XRDS')
service_tag = mkXRDTag('Service')
xrd_tag = mkXRDTag('XRD')
type_tag = mkXRDTag('Type')
uri_tag = mkXRDTag('URI')
expires_tag = mkXRDTag('Expires')

# Other XRD tags
canonicalID_tag = mkXRDTag('CanonicalID')


def isXRDS(xrd_tree):
    """Is this document an XRDS document?"""
    root = xrd_tree.getroot()
    return root.tag == root_tag


def getYadisXRD(xrd_tree):
    """Return the XRD element that should contain the Yadis services"""
    xrd = None

    # for the side-effect of assigning the last one in the list to the
    # xrd variable
    for xrd in xrd_tree.findall(xrd_tag):
        pass

    # There were no elements found, or else xrd would be set to the
    # last one
    if xrd is None:
        raise XRDSError('No XRD present in tree')

    return xrd


def getXRDExpiration(xrd_element, default=None):
    """Return the expiration date of this XRD element, or None if no
    expiration was specified.

    @type xrd_element: ElementTree node

    @param default: The value to use as the expiration if no
        expiration was specified in the XRD.

    @rtype: datetime.datetime

    @raises ValueError: If the xrd:Expires element is present, but its
        contents are not formatted according to the specification.
    """
    expires_element = xrd_element.find(expires_tag)
    if expires_element is None:
        return default
    else:
        expires_string = expires_element.text

        # Will raise ValueError if the string is not the expected format
        expires_time = strptime(expires_string, "%Y-%m-%dT%H:%M:%SZ")
        return datetime(*expires_time[0:6])


def getCanonicalID(iname, xrd_tree):
    """Return the CanonicalID from this XRDS document.

    @param iname: the XRI being resolved.
    @type iname: unicode

    @param xrd_tree: The XRDS output from the resolver.
    @type xrd_tree: ElementTree

    @returns: The XRI CanonicalID or None.
    @returntype: unicode or None
    """
    xrd_list = xrd_tree.findall(xrd_tag)
    xrd_list.reverse()

    try:
        canonicalID = xri.XRI(xrd_list[0].findall(canonicalID_tag)[0].text)
    except IndexError:
        return None

    childID = canonicalID.lower()

    for xrd in xrd_list[1:]:
        parent_sought = childID.rsplit("!", 1)[0]
        parent = xri.XRI(xrd.findtext(canonicalID_tag))
        if parent_sought != parent.lower():
            raise XRDSFraud("%r can not come from %s" % (childID, parent))

        childID = parent_sought

    root = xri.rootAuthority(iname)
    if not xri.providerIsAuthoritative(root, childID):
        raise XRDSFraud("%r can not come from root %r" % (childID, root))

    return canonicalID


@functools.total_ordering
class _Max(object):
    """
    Value that compares greater than any other value.

    Should only be used as a singleton. Implemented for use as a
    priority value for when a priority is not specified.
    """

    def __lt__(self, other):
        return isinstance(other, self.__class__)

    def __eq__(self, other):
        return isinstance(other, self.__class__)


Max = _Max()


def getPriorityStrict(element):
    """Get the priority of this element.

    Raises ValueError if the value of the priority is invalid. If no
    priority is specified, it returns a value that compares greater
    than any other value.
    """
    prio_str = element.get('priority')
    if prio_str is not None:
        prio_val = int(prio_str)
        if prio_val >= 0:
            return prio_val
        else:
            raise ValueError('Priority values must be non-negative integers')

    # Any errors in parsing the priority fall through to here
    return Max


def getPriority(element):
    """Get the priority of this element

    Returns Max if no priority is specified or the priority value is invalid.
    """
    try:
        return getPriorityStrict(element)
    except ValueError:
        return Max


def prioSort(elements):
    """Sort a list of elements that have priority attributes"""
    # Randomize the services before sorting so that equal priority
    # elements are load-balanced.
    random.shuffle(elements)

    sorted_elems = sorted(elements, key=getPriority)
    return sorted_elems


def iterServices(xrd_tree):
    """Return an iterable over the Service elements in the Yadis XRD

    sorted by priority"""
    xrd = getYadisXRD(xrd_tree)
    return prioSort(xrd.findall(service_tag))


def sortedURIs(service_element):
    """Given a Service element, return a list of the contents of all
    URI tags in priority order."""
    return [
        uri_element.text
        for uri_element in prioSort(service_element.findall(uri_tag))
    ]


def getTypeURIs(service_element):
    """Given a Service element, return a list of the contents of all
    Type tags"""
    return [
        type_element.text for type_element in service_element.findall(type_tag)
    ]


def expandService(service_element):
    """Take a service element and expand it into an iterator of:
    ([type_uri], uri, service_element)
    """
    uris = sortedURIs(service_element)
    if not uris:
        uris = [None]

    expanded = []
    for uri in uris:
        type_uris = getTypeURIs(service_element)
        expanded.append((type_uris, uri, service_element))

    return expanded


def expandServices(service_elements):
    """Take a sorted iterator of service elements and expand it into a
    sorted iterator of:
    ([type_uri], uri, service_element)

    There may be more than one item in the resulting list for each
    service element if there is more than one URI or type for a
    service, but each triple will be unique.

    If there is no URI or Type for a Service element, it will not
    appear in the result.
    """
    expanded = []
    for service_element in service_elements:
        expanded.extend(expandService(service_element))

    return expanded
