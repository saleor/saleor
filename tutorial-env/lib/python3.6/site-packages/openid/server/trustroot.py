# -*- test-case-name: openid.test.test_rpverify -*-
"""
This module contains the C{L{TrustRoot}} class, which helps handle
trust root checking.  This module is used by the
C{L{openid.server.server}} module, but it is also available to server
implementers who wish to use it for additional trust root checking.

It also implements relying party return_to URL verification, based on
the realm.
"""

__all__ = [
    'TrustRoot',
    'RP_RETURN_TO_URL_TYPE',
    'extractReturnToURLs',
    'returnToMatches',
    'verifyReturnTo',
]

from openid import urinorm
from openid.yadis import services

from urllib.parse import urlparse, urlunparse
import re
import logging

############################################
_protocols = ['http', 'https']
_top_level_domains = [
    'ac', 'ad', 'ae', 'aero', 'af', 'ag', 'ai', 'al', 'am', 'an', 'ao', 'aq',
    'ar', 'arpa', 'as', 'asia', 'at', 'au', 'aw', 'ax', 'az', 'ba', 'bb', 'bd',
    'be', 'bf', 'bg', 'bh', 'bi', 'biz', 'bj', 'bm', 'bn', 'bo', 'br', 'bs',
    'bt', 'bv', 'bw', 'by', 'bz', 'ca', 'cat', 'cc', 'cd', 'cf', 'cg', 'ch',
    'ci', 'ck', 'cl', 'cm', 'cn', 'co', 'com', 'coop', 'cr', 'cu', 'cv', 'cx',
    'cy', 'cz', 'de', 'dj', 'dk', 'dm', 'do', 'dz', 'ec', 'edu', 'ee', 'eg',
    'er', 'es', 'et', 'eu', 'fi', 'fj', 'fk', 'fm', 'fo', 'fr', 'ga', 'gb',
    'gd', 'ge', 'gf', 'gg', 'gh', 'gi', 'gl', 'gm', 'gn', 'gov', 'gp', 'gq',
    'gr', 'gs', 'gt', 'gu', 'gw', 'gy', 'hk', 'hm', 'hn', 'hr', 'ht', 'hu',
    'id', 'ie', 'il', 'im', 'in', 'info', 'int', 'io', 'iq', 'ir', 'is', 'it',
    'je', 'jm', 'jo', 'jobs', 'jp', 'ke', 'kg', 'kh', 'ki', 'km', 'kn', 'kp',
    'kr', 'kw', 'ky', 'kz', 'la', 'lb', 'lc', 'li', 'lk', 'lr', 'ls', 'lt',
    'lu', 'lv', 'ly', 'ma', 'mc', 'md', 'me', 'mg', 'mh', 'mil', 'mk', 'ml',
    'mm', 'mn', 'mo', 'mobi', 'mp', 'mq', 'mr', 'ms', 'mt', 'mu', 'museum',
    'mv', 'mw', 'mx', 'my', 'mz', 'na', 'name', 'nc', 'ne', 'net', 'nf', 'ng',
    'ni', 'nl', 'no', 'np', 'nr', 'nu', 'nz', 'om', 'org', 'pa', 'pe', 'pf',
    'pg', 'ph', 'pk', 'pl', 'pm', 'pn', 'pr', 'pro', 'ps', 'pt', 'pw', 'py',
    'qa', 're', 'ro', 'rs', 'ru', 'rw', 'sa', 'sb', 'sc', 'sd', 'se', 'sg',
    'sh', 'si', 'sj', 'sk', 'sl', 'sm', 'sn', 'so', 'sr', 'st', 'su', 'sv',
    'sy', 'sz', 'tc', 'td', 'tel', 'tf', 'tg', 'th', 'tj', 'tk', 'tl', 'tm',
    'tn', 'to', 'tp', 'tr', 'travel', 'tt', 'tv', 'tw', 'tz', 'ua', 'ug', 'uk',
    'us', 'uy', 'uz', 'va', 'vc', 've', 'vg', 'vi', 'vn', 'vu', 'wf', 'ws',
    'xn--0zwm56d', 'xn--11b5bs3a9aj6g', 'xn--80akhbyknj4f', 'xn--9t4b11yi5a',
    'xn--deba0ad', 'xn--g6w251d', 'xn--hgbk6aj7f53bba', 'xn--hlcj6aya9esc7a',
    'xn--jxalpdlp', 'xn--kgbechtv', 'xn--zckzah', 'ye', 'yt', 'yu', 'za', 'zm',
    'zw'
]

# Build from RFC3986, section 3.2.2. Used to reject hosts with invalid
# characters.
host_segment_re = re.compile(
    r"(?:[-a-zA-Z0-9!$&'\(\)\*+,;=._~]|%[a-zA-Z0-9]{2})+$")


class RealmVerificationRedirected(Exception):
    """Attempting to verify this realm resulted in a redirect.

    @since: 2.1.0
    """

    def __init__(self, relying_party_url, rp_url_after_redirects):
        self.relying_party_url = relying_party_url
        self.rp_url_after_redirects = rp_url_after_redirects

    def __str__(self):
        return ("Attempting to verify %r resulted in "
                "redirect to %r" % (self.relying_party_url,
                                    self.rp_url_after_redirects))


def _parseURL(url):
    try:
        url = urinorm.urinorm(url)
    except ValueError:
        return None
    proto, netloc, path, params, query, frag = urlparse(url)
    if not path:
        # Python <2.4 does not parse URLs with no path properly
        if not query and '?' in netloc:
            netloc, query = netloc.split('?', 1)

        path = '/'

    path = urlunparse(('', '', path, params, query, frag))

    if ':' in netloc:
        try:
            host, port = netloc.split(':')
        except ValueError:
            return None

        if not re.match(r'\d+$', port):
            return None
    else:
        host = netloc
        port = ''

    host = host.lower()
    if not host_segment_re.match(host):
        return None

    return proto, host, port, path


class TrustRoot(object):
    """
    This class represents an OpenID trust root.  The C{L{parse}}
    classmethod accepts a trust root string, producing a
    C{L{TrustRoot}} object.  The method OpenID server implementers
    would be most likely to use is the C{L{isSane}} method, which
    checks the trust root for given patterns that indicate that the
    trust root is too broad or points to a local network resource.

    @sort: parse, isSane
    """

    def __init__(self, unparsed, proto, wildcard, host, port, path):
        self.unparsed = unparsed
        self.proto = proto
        self.wildcard = wildcard
        self.host = host
        self.port = port
        self.path = path

    def isSane(self):
        """
        This method checks the to see if a trust root represents a
        reasonable (sane) set of URLs.  'http://*.com/', for example
        is not a reasonable pattern, as it cannot meaningfully specify
        the site claiming it.  This function attempts to find many
        related examples, but it can only work via heuristics.
        Negative responses from this method should be treated as
        advisory, used only to alert the user to examine the trust
        root carefully.


        @return: Whether the trust root is sane

        @rtype: C{bool}
        """

        if self.host == 'localhost':
            return True

        host_parts = self.host.split('.')
        if self.wildcard:
            assert host_parts[0] == '', host_parts
            del host_parts[0]

        # If it's an absolute domain name, remove the empty string
        # from the end.
        if host_parts and not host_parts[-1]:
            del host_parts[-1]

        if not host_parts:
            return False

        # Do not allow adjacent dots
        if '' in host_parts:
            return False

        tld = host_parts[-1]
        if tld not in _top_level_domains:
            return False

        if len(host_parts) == 1:
            return False

        if self.wildcard:
            if len(tld) == 2 and len(host_parts[-2]) <= 3:
                # It's a 2-letter tld with a short second to last segment
                # so there needs to be more than two segments specified
                # (e.g. *.co.uk is insane)
                return len(host_parts) > 2

        # Passed all tests for insanity.
        return True

    def validateURL(self, url):
        """
        Validates a URL against this trust root.


        @param url: The URL to check

        @type url: C{str}


        @return: Whether the given URL is within this trust root.

        @rtype: C{bool}
        """

        url_parts = _parseURL(url)
        if url_parts is None:
            return False

        proto, host, port, path = url_parts

        if proto != self.proto:
            return False

        if port != self.port:
            return False

        if '*' in host:
            return False

        if not self.wildcard:
            if host != self.host:
                return False
        elif ((not host.endswith(self.host)) and ('.' + host) != self.host):
            return False

        if path != self.path:
            path_len = len(self.path)
            trust_prefix = self.path[:path_len]
            url_prefix = path[:path_len]

            # must be equal up to the length of the path, at least
            if trust_prefix != url_prefix:
                return False

            # These characters must be on the boundary between the end
            # of the trust root's path and the start of the URL's
            # path.
            if '?' in self.path:
                allowed = '&'
            else:
                allowed = '?/'

            return (self.path[-1] in allowed or path[path_len] in allowed)

        return True

    def parse(cls, trust_root):
        """
        This method creates a C{L{TrustRoot}} instance from the given
        input, if possible.


        @param trust_root: This is the trust root to parse into a
        C{L{TrustRoot}} object.

        @type trust_root: C{str}


        @return: A C{L{TrustRoot}} instance if trust_root parses as a
        trust root, C{None} otherwise.

        @rtype: C{NoneType} or C{L{TrustRoot}}
        """
        url_parts = _parseURL(trust_root)
        if url_parts is None:
            return None

        proto, host, port, path = url_parts

        # check for valid prototype
        if proto not in _protocols:
            return None

        # check for URI fragment
        if path.find('#') != -1:
            return None

        # extract wildcard if it is there
        if host.find('*', 1) != -1:
            # wildcard must be at start of domain:  *.foo.com, not foo.*.com
            return None

        if host.startswith('*'):
            # Starts with star, so must have a dot after it (if a
            # domain is specified)
            if len(host) > 1 and host[1] != '.':
                return None

            host = host[1:]
            wilcard = True
        else:
            wilcard = False

        # we have a valid trust root
        tr = cls(trust_root, proto, wilcard, host, port, path)

        return tr

    parse = classmethod(parse)

    def checkSanity(cls, trust_root_string):
        """str -> bool

        is this a sane trust root?
        """
        trust_root = cls.parse(trust_root_string)
        if trust_root is None:
            return False
        else:
            return trust_root.isSane()

    checkSanity = classmethod(checkSanity)

    def checkURL(cls, trust_root, url):
        """quick func for validating a url against a trust root.  See the
        TrustRoot class if you need more control."""
        tr = cls.parse(trust_root)
        return tr is not None and tr.validateURL(url)

    checkURL = classmethod(checkURL)

    def buildDiscoveryURL(self):
        """Return a discovery URL for this realm.

        This function does not check to make sure that the realm is
        valid. Its behaviour on invalid inputs is undefined.

        @rtype: str

        @returns: The URL upon which relying party discovery should be run
            in order to verify the return_to URL

        @since: 2.1.0
        """
        if self.wildcard:
            # Use "www." in place of the star
            assert self.host.startswith('.'), self.host
            www_domain = 'www' + self.host
            return '%s://%s%s' % (self.proto, www_domain, self.path)
        else:
            return self.unparsed

    def __repr__(self):
        return "TrustRoot(%r, %r, %r, %r, %r, %r)" % (
            self.unparsed, self.proto, self.wildcard, self.host, self.port,
            self.path)

    def __str__(self):
        return repr(self)


# The URI for relying party discovery, used in realm verification.
#
# XXX: This should probably live somewhere else (like in
# openid.consumer or openid.yadis somewhere)
RP_RETURN_TO_URL_TYPE = 'http://specs.openid.net/auth/2.0/return_to'


def _extractReturnURL(endpoint):
    """If the endpoint is a relying party OpenID return_to endpoint,
    return the endpoint URL. Otherwise, return None.

    This function is intended to be used as a filter for the Yadis
    filtering interface.

    @see: C{L{openid.yadis.services}}
    @see: C{L{openid.yadis.filters}}

    @param endpoint: An XRDS BasicServiceEndpoint, as returned by
        performing Yadis dicovery.

    @returns: The endpoint URL or None if the endpoint is not a
        relying party endpoint.
    @rtype: str or NoneType
    """
    if endpoint.matchTypes([RP_RETURN_TO_URL_TYPE]):
        return endpoint.uri
    else:
        return None


def returnToMatches(allowed_return_to_urls, return_to):
    """Is the return_to URL under one of the supplied allowed
    return_to URLs?

    @since: 2.1.0
    """

    for allowed_return_to in allowed_return_to_urls:
        # A return_to pattern works the same as a realm, except that
        # it's not allowed to use a wildcard. We'll model this by
        # parsing it as a realm, and not trying to match it if it has
        # a wildcard.

        return_realm = TrustRoot.parse(allowed_return_to)
        if (  # Parses as a trust root
                return_realm is not None and

                # Does not have a wildcard
                not return_realm.wildcard and

                # Matches the return_to that we passed in with it
                return_realm.validateURL(return_to)):
            return True

    # No URL in the list matched
    return False


def getAllowedReturnURLs(relying_party_url):
    """Given a relying party discovery URL return a list of return_to URLs.

    @since: 2.1.0
    """
    (rp_url_after_redirects, return_to_urls) = services.getServiceEndpoints(
        relying_party_url, _extractReturnURL)

    if rp_url_after_redirects != relying_party_url:
        # Verification caused a redirect
        raise RealmVerificationRedirected(relying_party_url,
                                          rp_url_after_redirects)

    return return_to_urls


# _vrfy parameter is there to make testing easier
def verifyReturnTo(realm_str, return_to, _vrfy=getAllowedReturnURLs):
    """Verify that a return_to URL is valid for the given realm.

    This function builds a discovery URL, performs Yadis discovery on
    it, makes sure that the URL does not redirect, parses out the
    return_to URLs, and finally checks to see if the current return_to
    URL matches the return_to.

    @raises DiscoveryFailure: When Yadis discovery fails
    @returns: True if the return_to URL is valid for the realm

    @since: 2.1.0
    """
    realm = TrustRoot.parse(realm_str)
    if realm is None:
        # The realm does not parse as a URL pattern
        return False

    try:
        allowable_urls = _vrfy(realm.buildDiscoveryURL())
    except RealmVerificationRedirected as err:
        logging.exception(str(err))
        return False

    if returnToMatches(allowable_urls, return_to):
        return True
    else:
        logging.error("Failed to validate return_to %r for realm %r, was not "
                      "in %s" % (return_to, realm_str, allowable_urls))
        return False
