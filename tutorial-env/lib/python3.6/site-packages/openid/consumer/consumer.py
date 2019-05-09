# -*- test-case-name: openid.test.test_consumer -*-
"""OpenID support for Relying Parties (aka Consumers).

This module documents the main interface with the OpenID consumer
library.  The only part of the library which has to be used and isn't
documented in full here is the store required to create an
C{L{Consumer}} instance.  More on the abstract store type and
concrete implementations of it that are provided in the documentation
for the C{L{__init__<Consumer.__init__>}} method of the
C{L{Consumer}} class.


OVERVIEW
========

    The OpenID identity verification process most commonly uses the
    following steps, as visible to the user of this library:

        1. The user enters their OpenID into a field on the consumer's
           site, and hits a login button.

        2. The consumer site discovers the user's OpenID provider using
           the Yadis protocol.

        3. The consumer site sends the browser a redirect to the
           OpenID provider.  This is the authentication request as
           described in the OpenID specification.

        4. The OpenID provider's site sends the browser a redirect
           back to the consumer site.  This redirect contains the
           provider's response to the authentication request.

    The most important part of the flow to note is the consumer's site
    must handle two separate HTTP requests in order to perform the
    full identity check.


LIBRARY DESIGN
==============

    This consumer library is designed with that flow in mind.  The
    goal is to make it as easy as possible to perform the above steps
    securely.

    At a high level, there are two important parts in the consumer
    library.  The first important part is this module, which contains
    the interface to actually use this library.  The second is the
    C{L{openid.store.interface}} module, which describes the
    interface to use if you need to create a custom method for storing
    the state this library needs to maintain between requests.

    In general, the second part is less important for users of the
    library to know about, as several implementations are provided
    which cover a wide variety of situations in which consumers may
    use the library.

    This module contains a class, C{L{Consumer}}, with methods
    corresponding to the actions necessary in each of steps 2, 3, and
    4 described in the overview.  Use of this library should be as easy
    as creating an C{L{Consumer}} instance and calling the methods
    appropriate for the action the site wants to take.


SESSIONS, STORES, AND STATELESS MODE
====================================

    The C{L{Consumer}} object keeps track of two types of state:

        1. State of the user's current authentication attempt.  Things like
           the identity URL, the list of endpoints discovered for that
           URL, and in case where some endpoints are unreachable, the list
           of endpoints already tried.  This state needs to be held from
           Consumer.begin() to Consumer.complete(), but it is only applicable
           to a single session with a single user agent, and at the end of
           the authentication process (i.e. when an OP replies with either
           C{id_res} or C{cancel}) it may be discarded.

        2. State of relationships with servers, i.e. shared secrets
           (associations) with servers and nonces seen on signed messages.
           This information should persist from one session to the next and
           should not be bound to a particular user-agent.


    These two types of storage are reflected in the first two arguments of
    Consumer's constructor, C{session} and C{store}.  C{session} is a
    dict-like object and we hope your web framework provides you with one
    of these bound to the user agent.  C{store} is an instance of
    L{openid.store.interface.OpenIDStore}.

    Since the store does hold secrets shared between your application and the
    OpenID provider, you should be careful about how you use it in a shared
    hosting environment.  If the filesystem or database permissions of your
    web host allow strangers to read from them, do not store your data there!
    If you have no safe place to store your data, construct your consumer
    with C{None} for the store, and it will operate only in stateless mode.
    Stateless mode may be slower, put more load on the OpenID provider, and
    trusts the provider to keep you safe from replay attacks.


    Several store implementation are provided, and the interface is
    fully documented so that custom stores can be used as well.  See
    the documentation for the C{L{Consumer}} class for more
    information on the interface for stores.  The implementations that
    are provided allow the consumer site to store the necessary data
    in several different ways, including several SQL databases and
    normal files on disk.


IMMEDIATE MODE
==============

    In the flow described above, the user may need to confirm to the
    OpenID provider that it's ok to disclose his or her identity.
    The provider may draw pages asking for information from the user
    before it redirects the browser back to the consumer's site.  This
    is generally transparent to the consumer site, so it is typically
    ignored as an implementation detail.

    There can be times, however, where the consumer site wants to get
    a response immediately.  When this is the case, the consumer can
    put the library in immediate mode.  In immediate mode, there is an
    extra response possible from the server, which is essentially the
    server reporting that it doesn't have enough information to answer
    the question yet.


USING THIS LIBRARY
==================

    Integrating this library into an application is usually a
    relatively straightforward process.  The process should basically
    follow this plan:

    Add an OpenID login field somewhere on your site.  When an OpenID
    is entered in that field and the form is submitted, it should make
    a request to your site which includes that OpenID URL.

    First, the application should L{instantiate a Consumer<Consumer.__init__>}
    with a session for per-user state and store for shared state.
    using the store of choice.

    Next, the application should call the 'C{L{begin<Consumer.begin>}}' method on the
    C{L{Consumer}} instance.  This method takes the OpenID URL.  The
    C{L{begin<Consumer.begin>}} method returns an C{L{AuthRequest}}
    object.

    Next, the application should call the
    C{L{redirectURL<AuthRequest.redirectURL>}} method on the
    C{L{AuthRequest}} object.  The parameter C{return_to} is the URL
    that the OpenID server will send the user back to after attempting
    to verify his or her identity.  The C{realm} parameter is the
    URL (or URL pattern) that identifies your web site to the user
    when he or she is authorizing it.  Send a redirect to the
    resulting URL to the user's browser.

    That's the first half of the authentication process.  The second
    half of the process is done after the user's OpenID Provider sends the
    user's browser a redirect back to your site to complete their
    login.

    When that happens, the user will contact your site at the URL
    given as the C{return_to} URL to the
    C{L{redirectURL<AuthRequest.redirectURL>}} call made
    above.  The request will have several query parameters added to
    the URL by the OpenID provider as the information necessary to
    finish the request.

    Get a C{L{Consumer}} instance with the same session and store as
    before and call its C{L{complete<Consumer.complete>}} method,
    passing in all the received query arguments.

    There are multiple possible return types possible from that
    method. These indicate whether or not the login was successful,
    and include any additional information appropriate for their type.

@var SUCCESS: constant used as the status for
    L{SuccessResponse<openid.consumer.consumer.SuccessResponse>} objects.

@var FAILURE: constant used as the status for
    L{FailureResponse<openid.consumer.consumer.FailureResponse>} objects.

@var CANCEL: constant used as the status for
    L{CancelResponse<openid.consumer.consumer.CancelResponse>} objects.

@var SETUP_NEEDED: constant used as the status for
    L{SetupNeededResponse<openid.consumer.consumer.SetupNeededResponse>}
    objects.
"""

import copy
import logging
from urllib.parse import urlparse, urldefrag, parse_qsl

from openid import fetchers

from openid.consumer.discover import discover, OpenIDServiceEndpoint, \
     DiscoveryFailure, OPENID_1_0_TYPE, OPENID_1_1_TYPE, OPENID_2_0_TYPE
from openid.message import Message, OPENID_NS, OPENID2_NS, OPENID1_NS, \
     IDENTIFIER_SELECT, no_default, BARE_NS
from openid import cryptutil
from openid import oidutil
from openid.association import Association, default_negotiator, \
     SessionNegotiator
from openid.dh import DiffieHellman
from openid.store.nonce import mkNonce, split as splitNonce
from openid.yadis.manager import Discovery
from openid import urinorm

__all__ = [
    'AuthRequest',
    'Consumer',
    'SuccessResponse',
    'SetupNeededResponse',
    'CancelResponse',
    'FailureResponse',
    'SUCCESS',
    'FAILURE',
    'CANCEL',
    'SETUP_NEEDED',
]


def makeKVPost(request_message, server_url):
    """Make a Direct Request to an OpenID Provider and return the
    result as a Message object.

    @raises openid.fetchers.HTTPFetchingError: if an error is
        encountered in making the HTTP post.

    @rtype: L{openid.message.Message}
    """
    # XXX: TESTME
    resp = fetchers.fetch(server_url, body=request_message.toURLEncoded())

    # Process response in separate function that can be shared by async code.
    return _httpResponseToMessage(resp, server_url)


def _httpResponseToMessage(response, server_url):
    """Adapt a POST response to a Message.

    @type response: L{openid.fetchers.HTTPResponse}
    @param response: Result of a POST to an OpenID endpoint.

    @rtype: L{openid.message.Message}

    @raises openid.fetchers.HTTPFetchingError: if the server returned a
        status of other than 200 or 400.

    @raises ServerError: if the server returned an OpenID error.
    """
    # Should this function be named Message.fromHTTPResponse instead?
    response_message = Message.fromKVForm(response.body)
    if response.status == 400:
        raise ServerError.fromMessage(response_message)

    elif response.status not in (200, 206):
        fmt = 'bad status code from server %s: %s'
        error_message = fmt % (server_url, response.status)
        raise fetchers.HTTPFetchingError(error_message)

    return response_message


class Consumer(object):
    """An OpenID consumer implementation that performs discovery and
    does session management.

    @ivar consumer: an instance of an object implementing the OpenID
        protocol, but doing no discovery or session management.

    @type consumer: GenericConsumer

    @ivar session: A dictionary-like object representing the user's
        session data.  This is used for keeping state of the OpenID
        transaction when the user is redirected to the server.

    @cvar session_key_prefix: A string that is prepended to session
        keys to ensure that they are unique. This variable may be
        changed to suit your application.
    """
    session_key_prefix = "_openid_consumer_"

    _token = 'last_token'

    _discover = staticmethod(discover)

    def __init__(self, session, store, consumer_class=None):
        """Initialize a Consumer instance.

        You should create a new instance of the Consumer object with
        every HTTP request that handles OpenID transactions.

        @param session: See L{the session instance variable<openid.consumer.consumer.Consumer.session>}

        @param store: an object that implements the interface in
            C{L{openid.store.interface.OpenIDStore}}.  Several
            implementations are provided, to cover common database
            environments.

        @type store: C{L{openid.store.interface.OpenIDStore}}

        @see: L{openid.store.interface}
        @see: L{openid.store}
        """
        self.session = session
        if consumer_class is None:
            consumer_class = GenericConsumer
        self.consumer = consumer_class(store)
        self._token_key = self.session_key_prefix + self._token

    def begin(self, user_url, anonymous=False):
        """Start the OpenID authentication process. See steps 1-2 in
        the overview at the top of this file.

        @param user_url: Identity URL given by the user. This method
            performs a textual transformation of the URL to try and
            make sure it is normalized. For example, a user_url of
            example.com will be normalized to http://example.com/
            normalizing and resolving any redirects the server might
            issue.

        @type user_url: unicode

        @param anonymous: Whether to make an anonymous request of the OpenID
            provider.  Such a request does not ask for an authorization
            assertion for an OpenID identifier, but may be used with
            extensions to pass other data.  e.g. "I don't care who you are,
            but I'd like to know your time zone."

        @type anonymous: bool

        @returns: An object containing the discovered information will
            be returned, with a method for building a redirect URL to
            the server, as described in step 3 of the overview. This
            object may also be used to add extension arguments to the
            request, using its
            L{addExtensionArg<openid.consumer.consumer.AuthRequest.addExtensionArg>}
            method.

        @returntype: L{AuthRequest<openid.consumer.consumer.AuthRequest>}

        @raises openid.consumer.discover.DiscoveryFailure: when I fail to
            find an OpenID server for this URL.  If the C{yadis} package
            is available, L{openid.consumer.discover.DiscoveryFailure} is
            an alias for C{yadis.discover.DiscoveryFailure}.
        """
        disco = Discovery(self.session, user_url, self.session_key_prefix)
        try:
            service = disco.getNextService(self._discover)
        except fetchers.HTTPFetchingError as why:
            raise DiscoveryFailure('Error fetching XRDS document: %s' %
                                   (why.why, ), None)

        if service is None:
            raise DiscoveryFailure('No usable OpenID services found for %s' %
                                   (user_url, ), None)
        else:
            return self.beginWithoutDiscovery(service, anonymous)

    def beginWithoutDiscovery(self, service, anonymous=False):
        """Start OpenID verification without doing OpenID server
        discovery. This method is used internally by Consumer.begin
        after discovery is performed, and exists to provide an
        interface for library users needing to perform their own
        discovery.

        @param service: an OpenID service endpoint descriptor.  This
            object and factories for it are found in the
            L{openid.consumer.discover} module.

        @type service:
            L{OpenIDServiceEndpoint<openid.consumer.discover.OpenIDServiceEndpoint>}

        @returns: an OpenID authentication request object.

        @rtype: L{AuthRequest<openid.consumer.consumer.AuthRequest>}

        @See: Openid.consumer.consumer.Consumer.begin
        @see: openid.consumer.discover
        """
        auth_req = self.consumer.begin(service)
        self.session[self._token_key] = auth_req.endpoint

        try:
            auth_req.setAnonymous(anonymous)
        except ValueError as why:
            raise ProtocolError(str(why))

        return auth_req

    def complete(self, query, current_url):
        """Called to interpret the server's response to an OpenID
        request. It is called in step 4 of the flow described in the
        consumer overview.

        @param query: A dictionary of the query parameters for this
            HTTP request.

        @param current_url: The URL used to invoke the application.
            Extract the URL from your application's web
            request framework and specify it here to have it checked
            against the openid.return_to value in the response.  If
            the return_to URL check fails, the status of the
            completion will be FAILURE.

        @returns: a subclass of Response. The type of response is
            indicated by the status attribute, which will be one of
            SUCCESS, CANCEL, FAILURE, or SETUP_NEEDED.

        @see: L{SuccessResponse<openid.consumer.consumer.SuccessResponse>}
        @see: L{CancelResponse<openid.consumer.consumer.CancelResponse>}
        @see: L{SetupNeededResponse<openid.consumer.consumer.SetupNeededResponse>}
        @see: L{FailureResponse<openid.consumer.consumer.FailureResponse>}
        """

        endpoint = self.session.get(self._token_key)

        message = Message.fromPostArgs(query)
        response = self.consumer.complete(message, endpoint, current_url)

        try:
            del self.session[self._token_key]
        except KeyError:
            pass

        if (response.status in ['success', 'cancel'] and
                response.identity_url is not None):

            disco = Discovery(self.session, response.identity_url,
                              self.session_key_prefix)
            # This is OK to do even if we did not do discovery in
            # the first place.
            disco.cleanup(force=True)

        return response

    def setAssociationPreference(self, association_preferences):
        """Set the order in which association types/sessions should be
        attempted. For instance, to only allow HMAC-SHA256
        associations created with a DH-SHA256 association session:

        >>> consumer.setAssociationPreference([('HMAC-SHA256', 'DH-SHA256')])

        Any association type/association type pair that is not in this
        list will not be attempted at all.

        @param association_preferences: The list of allowed
            (association type, association session type) pairs that
            should be allowed for this consumer to use, in order from
            most preferred to least preferred.
        @type association_preferences: [(str, str)]

        @returns: None

        @see: C{L{openid.association.SessionNegotiator}}
        """
        self.consumer.negotiator = SessionNegotiator(association_preferences)


class DiffieHellmanSHA1ConsumerSession(object):
    session_type = 'DH-SHA1'
    hash_func = staticmethod(cryptutil.sha1)
    secret_size = 20
    allowed_assoc_types = ['HMAC-SHA1']

    def __init__(self, dh=None):
        if dh is None:
            dh = DiffieHellman.fromDefaults()

        self.dh = dh

    def getRequest(self):
        cpub = cryptutil.longToBase64(self.dh.public)

        args = {'dh_consumer_public': cpub}

        if not self.dh.usingDefaultValues():
            args.update({
                'dh_modulus': cryptutil.longToBase64(self.dh.modulus),
                'dh_gen': cryptutil.longToBase64(self.dh.generator),
            })

        return args

    def extractSecret(self, response):
        dh_server_public64 = response.getArg(OPENID_NS, 'dh_server_public',
                                             no_default)
        enc_mac_key64 = response.getArg(OPENID_NS, 'enc_mac_key', no_default)
        dh_server_public = cryptutil.base64ToLong(dh_server_public64)
        enc_mac_key = oidutil.fromBase64(enc_mac_key64)
        return self.dh.xorSecret(dh_server_public, enc_mac_key, self.hash_func)


class DiffieHellmanSHA256ConsumerSession(DiffieHellmanSHA1ConsumerSession):
    session_type = 'DH-SHA256'
    hash_func = staticmethod(cryptutil.sha256)
    secret_size = 32
    allowed_assoc_types = ['HMAC-SHA256']


class PlainTextConsumerSession(object):
    session_type = 'no-encryption'
    allowed_assoc_types = ['HMAC-SHA1', 'HMAC-SHA256']

    def getRequest(self):
        return {}

    def extractSecret(self, response):
        mac_key64 = response.getArg(OPENID_NS, 'mac_key', no_default)
        return oidutil.fromBase64(mac_key64)


class SetupNeededError(Exception):
    """Internally-used exception that indicates that an immediate-mode
    request cancelled."""

    def __init__(self, user_setup_url=None):
        Exception.__init__(self, user_setup_url)
        self.user_setup_url = user_setup_url


class ProtocolError(ValueError):
    """Exception that indicates that a message violated the
    protocol. It is raised and caught internally to this file."""


class TypeURIMismatch(ProtocolError):
    """A protocol error arising from type URIs mismatching
    """

    def __init__(self, expected, endpoint):
        ProtocolError.__init__(self, expected, endpoint)
        self.expected = expected
        self.endpoint = endpoint

    def __str__(self):
        s = '<%s.%s: Required type %s not found in %s for endpoint %s>' % (
            self.__class__.__module__, self.__class__.__name__, self.expected,
            self.endpoint.type_uris, self.endpoint)
        return s


class ServerError(Exception):
    """Exception that is raised when the server returns a 400 response
    code to a direct request."""

    def __init__(self, error_text, error_code, message):
        Exception.__init__(self, error_text)
        self.error_text = error_text
        self.error_code = error_code
        self.message = message

    def fromMessage(cls, message):
        """Generate a ServerError instance, extracting the error text
        and the error code from the message."""
        error_text = message.getArg(OPENID_NS, 'error',
                                    '<no error message supplied>')
        error_code = message.getArg(OPENID_NS, 'error_code')
        return cls(error_text, error_code, message)

    fromMessage = classmethod(fromMessage)


class GenericConsumer(object):
    """This is the implementation of the common logic for OpenID
    consumers. It is unaware of the application in which it is
    running.

    @ivar negotiator: An object that controls the kind of associations
        that the consumer makes. It defaults to
        C{L{openid.association.default_negotiator}}. Assign a
        different negotiator to it if you have specific requirements
        for how associations are made.
    @type negotiator: C{L{openid.association.SessionNegotiator}}
    """

    # The name of the query parameter that gets added to the return_to
    # URL when using OpenID1. You can change this value if you want or
    # need a different name, but don't make it start with openid,
    # because it's not a standard protocol thing for OpenID1. For
    # OpenID2, the library will take care of the nonce using standard
    # OpenID query parameter names.
    openid1_nonce_query_arg_name = 'janrain_nonce'

    # Another query parameter that gets added to the return_to for
    # OpenID 1; if the user's session state is lost, use this claimed
    # identifier to do discovery when verifying the response.
    openid1_return_to_identifier_name = 'openid1_claimed_id'

    session_types = {
        'DH-SHA1': DiffieHellmanSHA1ConsumerSession,
        'DH-SHA256': DiffieHellmanSHA256ConsumerSession,
        'no-encryption': PlainTextConsumerSession,
    }

    _discover = staticmethod(discover)

    def __init__(self, store):
        self.store = store
        self.negotiator = default_negotiator.copy()

    def begin(self, service_endpoint):
        """Create an AuthRequest object for the specified
        service_endpoint. This method will create an association if
        necessary."""
        if self.store is None:
            assoc = None
        else:
            assoc = self._getAssociation(service_endpoint)

        request = AuthRequest(service_endpoint, assoc)
        request.return_to_args[self.openid1_nonce_query_arg_name] = mkNonce()

        if request.message.isOpenID1():
            request.return_to_args[self.openid1_return_to_identifier_name] = \
                request.endpoint.claimed_id

        return request

    def complete(self, message, endpoint, return_to):
        """Process the OpenID message, using the specified endpoint
        and return_to URL as context. This method will handle any
        OpenID message that is sent to the return_to URL.
        """
        mode = message.getArg(OPENID_NS, 'mode', '<No mode set>')

        modeMethod = getattr(self, '_complete_' + mode, self._completeInvalid)

        return modeMethod(message, endpoint, return_to)

    def _complete_cancel(self, message, endpoint, _):
        return CancelResponse(endpoint)

    def _complete_error(self, message, endpoint, _):
        error = message.getArg(OPENID_NS, 'error')
        contact = message.getArg(OPENID_NS, 'contact')
        reference = message.getArg(OPENID_NS, 'reference')

        return FailureResponse(
            endpoint, error, contact=contact, reference=reference)

    def _complete_setup_needed(self, message, endpoint, _):
        if not message.isOpenID2():
            return self._completeInvalid(message, endpoint, _)

        user_setup_url = message.getArg(OPENID2_NS, 'user_setup_url')
        return SetupNeededResponse(endpoint, user_setup_url)

    def _complete_id_res(self, message, endpoint, return_to):
        try:
            self._checkSetupNeeded(message)
        except SetupNeededError as why:
            return SetupNeededResponse(endpoint, why.user_setup_url)
        else:
            try:
                return self._doIdRes(message, endpoint, return_to)
            except (ProtocolError, DiscoveryFailure) as why:
                return FailureResponse(endpoint, why)

    def _completeInvalid(self, message, endpoint, _):
        mode = message.getArg(OPENID_NS, 'mode', '<No mode set>')
        return FailureResponse(endpoint, 'Invalid openid.mode: %r' % (mode, ))

    def _checkReturnTo(self, message, return_to):
        """Check an OpenID message and its openid.return_to value
        against a return_to URL from an application.  Return True on
        success, False on failure.
        """
        # Check the openid.return_to args against args in the original
        # message.
        try:
            self._verifyReturnToArgs(message.toPostArgs())
        except ProtocolError as why:
            logging.exception("Verifying return_to arguments: %s" % (why, ))
            return False

        # Check the return_to base URL against the one in the message.
        msg_return_to = message.getArg(OPENID_NS, 'return_to')

        # The URL scheme, authority, and path MUST be the same between
        # the two URLs.
        app_parts = urlparse(urinorm.urinorm(return_to))
        msg_parts = urlparse(urinorm.urinorm(msg_return_to))

        # (addressing scheme, network location, path) must be equal in
        # both URLs.
        for part in range(0, 3):
            if app_parts[part] != msg_parts[part]:
                return False

        return True

    _makeKVPost = staticmethod(makeKVPost)

    def _checkSetupNeeded(self, message):
        """Check an id_res message to see if it is a
        checkid_immediate cancel response.

        @raises SetupNeededError: if it is a checkid_immediate cancellation
        """
        # In OpenID 1, we check to see if this is a cancel from
        # immediate mode by the presence of the user_setup_url
        # parameter.
        if message.isOpenID1():
            user_setup_url = message.getArg(OPENID1_NS, 'user_setup_url')
            if user_setup_url is not None:
                raise SetupNeededError(user_setup_url)

    def _doIdRes(self, message, endpoint, return_to):
        """Handle id_res responses that are not cancellations of
        immediate mode requests.

        @param message: the response paramaters.
        @param endpoint: the discovered endpoint object. May be None.

        @raises ProtocolError: If the message contents are not
            well-formed according to the OpenID specification. This
            includes missing fields or not signing fields that should
            be signed.

        @raises DiscoveryFailure: If the subject of the id_res message
            does not match the supplied endpoint, and discovery on the
            identifier in the message fails (this should only happen
            when using OpenID 2)

        @returntype: L{Response}
        """
        # Checks for presence of appropriate fields (and checks
        # signed list fields)
        self._idResCheckForFields(message)

        if not self._checkReturnTo(message, return_to):
            raise ProtocolError(
                "return_to does not match return URL. Expected %r, got %r" %
                (return_to, message.getArg(OPENID_NS, 'return_to')))

        # Verify discovery information:
        endpoint = self._verifyDiscoveryResults(message, endpoint)
        logging.info("Received id_res response from %s using association %s" %
                     (endpoint.server_url,
                      message.getArg(OPENID_NS, 'assoc_handle')))

        self._idResCheckSignature(message, endpoint.server_url)

        # Will raise a ProtocolError if the nonce is bad
        self._idResCheckNonce(message, endpoint)

        signed_list_str = message.getArg(OPENID_NS, 'signed', no_default)
        signed_list = signed_list_str.split(',')
        signed_fields = ["openid." + s for s in signed_list]
        return SuccessResponse(endpoint, message, signed_fields)

    def _idResGetNonceOpenID1(self, message, endpoint):
        """Extract the nonce from an OpenID 1 response.  Return the
        nonce from the BARE_NS since we independently check the
        return_to arguments are the same as those in the response
        message.

        See the openid1_nonce_query_arg_name class variable

        @returns: The nonce as a string or None
        """
        return message.getArg(BARE_NS, self.openid1_nonce_query_arg_name)

    def _idResCheckNonce(self, message, endpoint):
        if message.isOpenID1():
            # This indicates that the nonce was generated by the consumer
            nonce = self._idResGetNonceOpenID1(message, endpoint)
            server_url = ''
        else:
            nonce = message.getArg(OPENID2_NS, 'response_nonce')
            server_url = endpoint.server_url

        if nonce is None:
            raise ProtocolError('Nonce missing from response')

        try:
            timestamp, salt = splitNonce(nonce)
        except ValueError as why:
            raise ProtocolError('Malformed nonce: %s' % (why, ))

        if (self.store is not None and
                not self.store.useNonce(server_url, timestamp, salt)):
            raise ProtocolError('Nonce already used or out of range')

    def _idResCheckSignature(self, message, server_url):
        assoc_handle = message.getArg(OPENID_NS, 'assoc_handle')
        if self.store is None:
            assoc = None
        else:
            assoc = self.store.getAssociation(server_url, assoc_handle)

        if assoc:
            if assoc.expiresIn <= 0:
                # XXX: It might be a good idea sometimes to re-start the
                # authentication with a new association. Doing it
                # automatically opens the possibility for
                # denial-of-service by a server that just returns expired
                # associations (or really short-lived associations)
                raise ProtocolError('Association with %s expired' %
                                    (server_url, ))

            if not assoc.checkMessageSignature(message):
                raise ProtocolError('Bad signature')

        else:
            # It's not an association we know about.  Stateless mode is our
            # only possible path for recovery.
            # XXX - async framework will not want to block on this call to
            # _checkAuth.
            if not self._checkAuth(message, server_url):
                raise ProtocolError('Server denied check_authentication')

    def _idResCheckForFields(self, message):
        # XXX: this should be handled by the code that processes the
        # response (that is, if a field is missing, we should not have
        # to explicitly check that it's present, just make sure that
        # the fields are actually being used by the rest of the code
        # in tests). Although, which fields are signed does need to be
        # checked somewhere.
        basic_fields = ['return_to', 'assoc_handle', 'sig', 'signed']
        basic_sig_fields = ['return_to', 'identity']

        require_fields = {
            OPENID2_NS: basic_fields + ['op_endpoint'],
            OPENID1_NS: basic_fields + ['identity'],
        }

        require_sigs = {
            OPENID2_NS:
            basic_sig_fields +
            ['response_nonce', 'claimed_id', 'assoc_handle', 'op_endpoint'],
            OPENID1_NS:
            basic_sig_fields,
        }

        for field in require_fields[message.getOpenIDNamespace()]:
            if not message.hasKey(OPENID_NS, field):
                raise ProtocolError('Missing required field %r' % (field, ))

        signed_list_str = message.getArg(OPENID_NS, 'signed', no_default)
        signed_list = signed_list_str.split(',')

        for field in require_sigs[message.getOpenIDNamespace()]:
            # Field is present and not in signed list
            if message.hasKey(OPENID_NS, field) and field not in signed_list:
                raise ProtocolError('"%s" not signed' % (field, ))

    def _verifyReturnToArgs(query):
        """Verify that the arguments in the return_to URL are present in this
        response.
        """
        # NOTE -- query came from Message.toPostArgs, which returns a dict of
        # {str: str}
        message = Message.fromPostArgs(query)
        return_to = message.getArg(OPENID_NS, 'return_to')

        if return_to is None:
            raise ProtocolError('Response has no return_to')

        parsed_url = urlparse(return_to)
        rt_query = parsed_url[4]
        parsed_args = parse_qsl(rt_query)

        # NOTE -- parsed_args will be a dict of {bytes: bytes}, however it
        # will be checked against return values from Message methods which are
        # {str: str}. We need to compare apples to apples.
        for rt_key, rt_value in parsed_args:
            try:
                value = query[rt_key]
                if rt_value != value:
                    format = ("parameter %s value %r does not match "
                              "return_to's value %r")
                    raise ProtocolError(format % (rt_key, value, rt_value))
            except KeyError:
                format = "return_to parameter %s absent from query %r"
                raise ProtocolError(format % (rt_key, query))

        # Make sure all non-OpenID arguments in the response are also
        # in the signed return_to.
        bare_args = message.getArgs(BARE_NS)
        for pair in bare_args.items():
            if pair not in parsed_args:
                raise ProtocolError("Parameter %s not in return_to URL" %
                                    (pair[0], ))

    _verifyReturnToArgs = staticmethod(_verifyReturnToArgs)

    def _verifyDiscoveryResults(self, resp_msg, endpoint=None):
        """
        Extract the information from an OpenID assertion message and
        verify it against the original

        @param endpoint: The endpoint that resulted from doing discovery
        @param resp_msg: The id_res message object

        @returns: the verified endpoint
        """
        if resp_msg.getOpenIDNamespace() == OPENID2_NS:
            return self._verifyDiscoveryResultsOpenID2(resp_msg, endpoint)
        else:
            return self._verifyDiscoveryResultsOpenID1(resp_msg, endpoint)

    def _verifyDiscoveryResultsOpenID2(self, resp_msg, endpoint):
        to_match = OpenIDServiceEndpoint()
        to_match.type_uris = [OPENID_2_0_TYPE]
        to_match.claimed_id = resp_msg.getArg(OPENID2_NS, 'claimed_id')
        to_match.local_id = resp_msg.getArg(OPENID2_NS, 'identity')

        # Raises a KeyError when the op_endpoint is not present
        to_match.server_url = resp_msg.getArg(OPENID2_NS, 'op_endpoint',
                                              no_default)

        # claimed_id and identifier must both be present or both
        # be absent
        if (to_match.claimed_id is None and to_match.local_id is not None):
            raise ProtocolError(
                'openid.identity is present without openid.claimed_id')

        elif (to_match.claimed_id is not None and to_match.local_id is None):
            raise ProtocolError(
                'openid.claimed_id is present without openid.identity')

        # This is a response without identifiers, so there's really no
        # checking that we can do, so return an endpoint that's for
        # the specified `openid.op_endpoint'
        elif to_match.claimed_id is None:
            return OpenIDServiceEndpoint.fromOPEndpointURL(to_match.server_url)

        # The claimed ID doesn't match, so we have to do discovery
        # again. This covers not using sessions, OP identifier
        # endpoints and responses that didn't match the original
        # request.
        if not endpoint:
            logging.info('No pre-discovered information supplied.')
            endpoint = self._discoverAndVerify(to_match.claimed_id, [to_match])
        elif endpoint.isOPIdentifier():
            logging.info(
                'Pre-discovered information based on OP-ID; need to rediscover.'
            )
            endpoint = self._discoverAndVerify(to_match.claimed_id, [to_match])
        else:
            # The claimed ID matches, so we use the endpoint that we
            # discovered in initiation. This should be the most common
            # case.
            try:
                self._verifyDiscoverySingle(endpoint, to_match)
            except ProtocolError as e:
                logging.exception(
                    "Error attempting to use stored discovery information: " +
                    str(e))
                logging.info("Attempting discovery to verify endpoint")
                endpoint = self._discoverAndVerify(to_match.claimed_id,
                                                   [to_match])

        # The endpoint we return should have the claimed ID from the
        # message we just verified, fragment and all.
        if endpoint.claimed_id != to_match.claimed_id:
            endpoint = copy.copy(endpoint)
            endpoint.claimed_id = to_match.claimed_id
        return endpoint

    def _verifyDiscoveryResultsOpenID1(self, resp_msg, endpoint):
        claimed_id = resp_msg.getArg(BARE_NS,
                                     self.openid1_return_to_identifier_name)

        if endpoint is None and claimed_id is None:
            raise RuntimeError(
                'When using OpenID 1, the claimed ID must be supplied, '
                'either by passing it through as a return_to parameter '
                'or by using a session, and supplied to the GenericConsumer '
                'as the argument to complete()')
        elif endpoint is not None and claimed_id is None:
            claimed_id = endpoint.claimed_id

        to_match = OpenIDServiceEndpoint()
        to_match.type_uris = [OPENID_1_1_TYPE]
        to_match.local_id = resp_msg.getArg(OPENID1_NS, 'identity')
        # Restore delegate information from the initiation phase
        to_match.claimed_id = claimed_id

        if to_match.local_id is None:
            raise ProtocolError('Missing required field openid.identity')

        to_match_1_0 = copy.copy(to_match)
        to_match_1_0.type_uris = [OPENID_1_0_TYPE]

        if endpoint is not None:
            try:
                try:
                    self._verifyDiscoverySingle(endpoint, to_match)
                except TypeURIMismatch:
                    self._verifyDiscoverySingle(endpoint, to_match_1_0)
            except ProtocolError as e:
                logging.exception(
                    "Error attempting to use stored discovery information: " +
                    str(e))
                logging.info("Attempting discovery to verify endpoint")
            else:
                return endpoint

        # Endpoint is either bad (failed verification) or None
        return self._discoverAndVerify(claimed_id, [to_match, to_match_1_0])

    def _verifyDiscoverySingle(self, endpoint, to_match):
        """Verify that the given endpoint matches the information
        extracted from the OpenID assertion, and raise an exception if
        there is a mismatch.

        @type endpoint: openid.consumer.discover.OpenIDServiceEndpoint
        @type to_match: openid.consumer.discover.OpenIDServiceEndpoint

        @rtype: NoneType

        @raises ProtocolError: when the endpoint does not match the
            discovered information.
        """
        # Every type URI that's in the to_match endpoint has to be
        # present in the discovered endpoint.
        for type_uri in to_match.type_uris:
            if not endpoint.usesExtension(type_uri):
                raise TypeURIMismatch(type_uri, endpoint)

        # Fragments do not influence discovery, so we can't compare a
        # claimed identifier with a fragment to discovered information.
        defragged_claimed_id, _ = urldefrag(to_match.claimed_id)
        if defragged_claimed_id != endpoint.claimed_id:
            raise ProtocolError(
                'Claimed ID does not match (different subjects!), '
                'Expected %s, got %s' %
                (defragged_claimed_id, endpoint.claimed_id))

        if to_match.getLocalID() != endpoint.getLocalID():
            raise ProtocolError('local_id mismatch. Expected %s, got %s' %
                                (to_match.getLocalID(), endpoint.getLocalID()))

        # If the server URL is None, this must be an OpenID 1
        # response, because op_endpoint is a required parameter in
        # OpenID 2. In that case, we don't actually care what the
        # discovered server_url is, because signature checking or
        # check_auth should take care of that check for us.
        if to_match.server_url is None:
            assert to_match.preferredNamespace() == OPENID1_NS, (
                """The code calling this must ensure that OpenID 2
                responses have a non-none `openid.op_endpoint' and
                that it is set as the `server_url' attribute of the
                `to_match' endpoint.""")

        elif to_match.server_url != endpoint.server_url:
            raise ProtocolError('OP Endpoint mismatch. Expected %s, got %s' %
                                (to_match.server_url, endpoint.server_url))

    def _discoverAndVerify(self, claimed_id, to_match_endpoints):
        """Given an endpoint object created from the information in an
        OpenID response, perform discovery and verify the discovery
        results, returning the matching endpoint that is the result of
        doing that discovery.

        @type to_match: openid.consumer.discover.OpenIDServiceEndpoint
        @param to_match: The endpoint whose information we're confirming

        @rtype: openid.consumer.discover.OpenIDServiceEndpoint
        @returns: The result of performing discovery on the claimed
            identifier in `to_match'

        @raises DiscoveryFailure: when discovery fails.
        """
        logging.info('Performing discovery on %s' % (claimed_id, ))
        _, services = self._discover(claimed_id)
        if not services:
            raise DiscoveryFailure('No OpenID information found at %s' %
                                   (claimed_id, ), None)
        return self._verifyDiscoveredServices(claimed_id, services,
                                              to_match_endpoints)

    def _verifyDiscoveredServices(self, claimed_id, services,
                                  to_match_endpoints):
        """See @L{_discoverAndVerify}"""

        # Search the services resulting from discovery to find one
        # that matches the information from the assertion
        failure_messages = []
        for endpoint in services:
            for to_match_endpoint in to_match_endpoints:
                try:
                    self._verifyDiscoverySingle(endpoint, to_match_endpoint)
                except ProtocolError as why:
                    failure_messages.append(str(why))
                else:
                    # It matches, so discover verification has
                    # succeeded. Return this endpoint.
                    return endpoint
        else:
            logging.error('Discovery verification failure for %s' %
                          (claimed_id, ))
            for failure_message in failure_messages:
                logging.error(' * Endpoint mismatch: ' + failure_message)

            raise DiscoveryFailure(
                'No matching endpoint found after discovering %s' %
                (claimed_id, ), None)

    def _checkAuth(self, message, server_url):
        """Make a check_authentication request to verify this message.

        @returns: True if the request is valid.
        @rtype: bool
        """
        logging.info('Using OpenID check_authentication')
        request = self._createCheckAuthRequest(message)
        if request is None:
            return False
        try:
            response = self._makeKVPost(request, server_url)
        except (fetchers.HTTPFetchingError, ServerError) as e:
            e0 = e.args[0]
            logging.exception('check_authentication failed: %s' % e0)
            return False
        else:
            return self._processCheckAuthResponse(response, server_url)

    def _createCheckAuthRequest(self, message):
        """Generate a check_authentication request message given an
        id_res message.
        """
        signed = message.getArg(OPENID_NS, 'signed')
        if signed:
            if isinstance(signed, bytes):
                signed = str(signed, encoding="utf-8")
            for k in signed.split(','):
                logging.info(k)
                val = message.getAliasedArg(k)

                # Signed value is missing
                if val is None:
                    logging.info('Missing signed field %r' % (k, ))
                    return None

        check_auth_message = message.copy()
        check_auth_message.setArg(OPENID_NS, 'mode', 'check_authentication')
        return check_auth_message

    def _processCheckAuthResponse(self, response, server_url):
        """Process the response message from a check_authentication
        request, invalidating associations if requested.
        """
        is_valid = response.getArg(OPENID_NS, 'is_valid', 'false')

        invalidate_handle = response.getArg(OPENID_NS, 'invalidate_handle')
        if invalidate_handle is not None:
            logging.info('Received "invalidate_handle" from server %s' %
                         (server_url, ))
            if self.store is None:
                logging.error('Unexpectedly got invalidate_handle without '
                              'a store!')
            else:
                self.store.removeAssociation(server_url, invalidate_handle)

        if is_valid == 'true':
            return True
        else:
            logging.error('Server responds that checkAuth call is not valid')
            return False

    def _getAssociation(self, endpoint):
        """Get an association for the endpoint's server_url.

        First try seeing if we have a good association in the
        store. If we do not, then attempt to negotiate an association
        with the server.

        If we negotiate a good association, it will get stored.

        @returns: A valid association for the endpoint's server_url or None
        @rtype: openid.association.Association or NoneType
        """
        assoc = self.store.getAssociation(endpoint.server_url)

        if assoc is None or assoc.expiresIn <= 0:
            assoc = self._negotiateAssociation(endpoint)
            if assoc is not None:
                self.store.storeAssociation(endpoint.server_url, assoc)

        return assoc

    def _negotiateAssociation(self, endpoint):
        """Make association requests to the server, attempting to
        create a new association.

        @returns: a new association object

        @rtype: L{openid.association.Association}
        """
        # Get our preferred session/association type from the negotiatior.
        assoc_type, session_type = self.negotiator.getAllowedType()

        try:
            assoc = self._requestAssociation(endpoint, assoc_type,
                                             session_type)
        except ServerError as why:
            supportedTypes = self._extractSupportedAssociationType(
                why, endpoint, assoc_type)
            if supportedTypes is not None:
                assoc_type, session_type = supportedTypes
                # Attempt to create an association from the assoc_type
                # and session_type that the server told us it
                # supported.
                try:
                    assoc = self._requestAssociation(endpoint, assoc_type,
                                                     session_type)
                except ServerError as why:
                    # Do not keep trying, since it rejected the
                    # association type that it told us to use.
                    logging.error(
                        'Server %s refused its suggested association '
                        'type: session_type=%s, assoc_type=%s' % (
                            endpoint.server_url, session_type, assoc_type))
                    return None
                else:
                    return assoc
        else:
            return assoc

    def _extractSupportedAssociationType(self, server_error, endpoint,
                                         assoc_type):
        """Handle ServerErrors resulting from association requests.

        @returns: If server replied with an C{unsupported-type} error,
            return a tuple of supported C{association_type}, C{session_type}.
            Otherwise logs the error and returns None.
        @rtype: tuple or None
        """
        # Any error message whose code is not 'unsupported-type'
        # should be considered a total failure.
        if server_error.error_code != 'unsupported-type' or \
               server_error.message.isOpenID1():
            logging.error(
                'Server error when requesting an association from %r: %s' %
                (endpoint.server_url, server_error.error_text))
            return None

        # The server didn't like the association/session type
        # that we sent, and it sent us back a message that
        # might tell us how to handle it.
        logging.error('Unsupported association type %s: %s' %
                      (assoc_type, server_error.error_text, ))

        # Extract the session_type and assoc_type from the
        # error message
        assoc_type = server_error.message.getArg(OPENID_NS, 'assoc_type')
        session_type = server_error.message.getArg(OPENID_NS, 'session_type')

        if assoc_type is None or session_type is None:
            logging.error('Server responded with unsupported association '
                          'session but did not supply a fallback.')
            return None
        elif not self.negotiator.isAllowed(assoc_type, session_type):
            fmt = ('Server sent unsupported session/association type: '
                   'session_type=%s, assoc_type=%s')
            logging.error(fmt % (session_type, assoc_type))
            return None
        else:
            return assoc_type, session_type

    def _requestAssociation(self, endpoint, assoc_type, session_type):
        """Make and process one association request to this endpoint's
        OP endpoint URL.

        @returns: An association object or None if the association
            processing failed.

        @raises ServerError: when the remote OpenID server returns an error.
        """
        assoc_session, args = self._createAssociateRequest(
            endpoint, assoc_type, session_type)

        try:
            response = self._makeKVPost(args, endpoint.server_url)
        except fetchers.HTTPFetchingError as why:
            logging.exception('openid.associate request failed: %s' % (why, ))
            return None

        try:
            assoc = self._extractAssociation(response, assoc_session)
        except KeyError as why:
            logging.exception(
                'Missing required parameter in response from %s: %s' %
                (endpoint.server_url, why))
            return None
        except ProtocolError as why:
            logging.exception('Protocol error parsing response from %s: %s' %
                              (endpoint.server_url, why))
            return None
        else:
            return assoc

    def _createAssociateRequest(self, endpoint, assoc_type, session_type):
        """Create an association request for the given assoc_type and
        session_type.

        @param endpoint: The endpoint whose server_url will be
            queried. The important bit about the endpoint is whether
            it's in compatiblity mode (OpenID 1.1)

        @param assoc_type: The association type that the request
            should ask for.
        @type assoc_type: str

        @param session_type: The session type that should be used in
            the association request. The session_type is used to
            create an association session object, and that session
            object is asked for any additional fields that it needs to
            add to the request.
        @type session_type: str

        @returns: a pair of the association session object and the
            request message that will be sent to the server.
        @rtype: (association session type (depends on session_type),
                 openid.message.Message)
        """
        session_type_class = self.session_types[session_type]
        assoc_session = session_type_class()

        args = {
            'mode': 'associate',
            'assoc_type': assoc_type,
        }

        if not endpoint.compatibilityMode():
            args['ns'] = OPENID2_NS

        # Leave out the session type if we're in compatibility mode
        # *and* it's no-encryption.
        if (not endpoint.compatibilityMode() or
                assoc_session.session_type != 'no-encryption'):
            args['session_type'] = assoc_session.session_type

        args.update(assoc_session.getRequest())
        message = Message.fromOpenIDArgs(args)
        return assoc_session, message

    def _getOpenID1SessionType(self, assoc_response):
        """Given an association response message, extract the OpenID
        1.X session type.

        This function mostly takes care of the 'no-encryption' default
        behavior in OpenID 1.

        If the association type is plain-text, this function will
        return 'no-encryption'

        @returns: The association type for this message
        @rtype: str

        @raises KeyError: when the session_type field is absent.
        """
        # If it's an OpenID 1 message, allow session_type to default
        # to None (which signifies "no-encryption")
        session_type = assoc_response.getArg(OPENID1_NS, 'session_type')

        # Handle the differences between no-encryption association
        # respones in OpenID 1 and 2:

        # no-encryption is not really a valid session type for
        # OpenID 1, but we'll accept it anyway, while issuing a
        # warning.
        if session_type == 'no-encryption':
            logging.warning('OpenID server sent "no-encryption"'
                            'for OpenID 1.X')

        # Missing or empty session type is the way to flag a
        # 'no-encryption' response. Change the session type to
        # 'no-encryption' so that it can be handled in the same
        # way as OpenID 2 'no-encryption' respones.
        elif session_type == '' or session_type is None:
            session_type = 'no-encryption'

        return session_type

    def _extractAssociation(self, assoc_response, assoc_session):
        """Attempt to extract an association from the response, given
        the association response message and the established
        association session.

        @param assoc_response: The association response message from
            the server
        @type assoc_response: openid.message.Message

        @param assoc_session: The association session object that was
            used when making the request
        @type assoc_session: depends on the session type of the request

        @raises ProtocolError: when data is malformed
        @raises KeyError: when a field is missing

        @rtype: openid.association.Association
        """
        # Extract the common fields from the response, raising an
        # exception if they are not found
        assoc_type = assoc_response.getArg(OPENID_NS, 'assoc_type', no_default)
        assoc_handle = assoc_response.getArg(OPENID_NS, 'assoc_handle',
                                             no_default)

        # expires_in is a base-10 string. The Python parsing will
        # accept literals that have whitespace around them and will
        # accept negative values. Neither of these are really in-spec,
        # but we think it's OK to accept them.
        expires_in_str = assoc_response.getArg(OPENID_NS, 'expires_in',
                                               no_default)
        try:
            expires_in = int(expires_in_str)
        except ValueError as why:
            raise ProtocolError('Invalid expires_in field: %s' % (why, ))

        # OpenID 1 has funny association session behaviour.
        if assoc_response.isOpenID1():
            session_type = self._getOpenID1SessionType(assoc_response)
        else:
            session_type = assoc_response.getArg(OPENID2_NS, 'session_type',
                                                 no_default)

        # Session type mismatch
        if assoc_session.session_type != session_type:
            if (assoc_response.isOpenID1() and
                    session_type == 'no-encryption'):
                # In OpenID 1, any association request can result in a
                # 'no-encryption' association response. Setting
                # assoc_session to a new no-encryption session should
                # make the rest of this function work properly for
                # that case.
                assoc_session = PlainTextConsumerSession()
            else:
                # Any other mismatch, regardless of protocol version
                # results in the failure of the association session
                # altogether.
                fmt = 'Session type mismatch. Expected %r, got %r'
                message = fmt % (assoc_session.session_type, session_type)
                raise ProtocolError(message)

        # Make sure assoc_type is valid for session_type
        if assoc_type not in assoc_session.allowed_assoc_types:
            fmt = 'Unsupported assoc_type for session %s returned: %s'
            raise ProtocolError(fmt % (assoc_session.session_type, assoc_type))

        # Delegate to the association session to extract the secret
        # from the response, however is appropriate for that session
        # type.
        try:
            secret = assoc_session.extractSecret(assoc_response)
        except ValueError as why:
            fmt = 'Malformed response for %s session: %s'
            raise ProtocolError(fmt % (assoc_session.session_type, why))

        return Association.fromExpiresIn(expires_in, assoc_handle, secret,
                                         assoc_type)


class AuthRequest(object):
    """An object that holds the state necessary for generating an
    OpenID authentication request. This object holds the association
    with the server and the discovered information with which the
    request will be made.

    It is separate from the consumer because you may wish to add
    things to the request before sending it on its way to the
    server. It also has serialization options that let you encode the
    authentication request as a URL or as a form POST.
    """

    def __init__(self, endpoint, assoc):
        """
        Creates a new AuthRequest object.  This just stores each
        argument in an appropriately named field.

        Users of this library should not create instances of this
        class.  Instances of this class are created by the library
        when needed.
        """
        self.assoc = assoc
        self.endpoint = endpoint
        self.return_to_args = {}
        self.message = Message(endpoint.preferredNamespace())
        self._anonymous = False

    def setAnonymous(self, is_anonymous):
        """Set whether this request should be made anonymously. If a
        request is anonymous, the identifier will not be sent in the
        request. This is only useful if you are making another kind of
        request with an extension in this request.

        Anonymous requests are not allowed when the request is made
        with OpenID 1.

        @raises ValueError: when attempting to set an OpenID1 request
            as anonymous
        """
        if is_anonymous and self.message.isOpenID1():
            raise ValueError('OpenID 1 requests MUST include the '
                             'identifier in the request')
        else:
            self._anonymous = is_anonymous

    def addExtension(self, extension_request):
        """Add an extension to this checkid request.

        @param extension_request: An object that implements the
            extension interface for adding arguments to an OpenID
            message.
        """
        extension_request.toMessage(self.message)

    def addExtensionArg(self, namespace, key, value):
        """Add an extension argument to this OpenID authentication
        request.

        Use caution when adding arguments, because they will be
        URL-escaped and appended to the redirect URL, which can easily
        get quite long.

        @param namespace: The namespace for the extension. For
            example, the simple registration extension uses the
            namespace C{sreg}.

        @type namespace: str

        @param key: The key within the extension namespace. For
            example, the nickname field in the simple registration
            extension's key is C{nickname}.

        @type key: str

        @param value: The value to provide to the server for this
            argument.

        @type value: str
        """
        self.message.setArg(namespace, key, value)

    def getMessage(self, realm, return_to=None, immediate=False):
        """Produce a L{openid.message.Message} representing this request.

        @param realm: The URL (or URL pattern) that identifies your
            web site to the user when she is authorizing it.

        @type realm: str

        @param return_to: The URL that the OpenID provider will send the
            user back to after attempting to verify her identity.

            Not specifying a return_to URL means that the user will not
            be returned to the site issuing the request upon its
            completion.

        @type return_to: str

        @param immediate: If True, the OpenID provider is to send back
            a response immediately, useful for behind-the-scenes
            authentication attempts.  Otherwise the OpenID provider
            may engage the user before providing a response.  This is
            the default case, as the user may need to provide
            credentials or approve the request before a positive
            response can be sent.

        @type immediate: bool

        @returntype: L{openid.message.Message}
        """
        if return_to:
            return_to = oidutil.appendArgs(return_to, self.return_to_args)
        elif immediate:
            raise ValueError(
                '"return_to" is mandatory when using "checkid_immediate"')
        elif self.message.isOpenID1():
            raise ValueError('"return_to" is mandatory for OpenID 1 requests')
        elif self.return_to_args:
            raise ValueError('extra "return_to" arguments were specified, '
                             'but no return_to was specified')

        if immediate:
            mode = 'checkid_immediate'
        else:
            mode = 'checkid_setup'

        message = self.message.copy()
        if message.isOpenID1():
            realm_key = 'trust_root'
        else:
            realm_key = 'realm'

        message.updateArgs(OPENID_NS, {
            realm_key: realm,
            'mode': mode,
            'return_to': return_to,
        })

        if not self._anonymous:
            if self.endpoint.isOPIdentifier():
                # This will never happen when we're in compatibility
                # mode, as long as isOPIdentifier() returns False
                # whenever preferredNamespace() returns OPENID1_NS.
                claimed_id = request_identity = IDENTIFIER_SELECT
            else:
                request_identity = self.endpoint.getLocalID()
                claimed_id = self.endpoint.claimed_id

            # This is true for both OpenID 1 and 2
            message.setArg(OPENID_NS, 'identity', request_identity)

            if message.isOpenID2():
                message.setArg(OPENID2_NS, 'claimed_id', claimed_id)

        if self.assoc:
            message.setArg(OPENID_NS, 'assoc_handle', self.assoc.handle)
            assoc_log_msg = 'with association %s' % (self.assoc.handle, )
        else:
            assoc_log_msg = 'using stateless mode.'

        logging.info("Generated %s request to %s %s" %
                     (mode, self.endpoint.server_url, assoc_log_msg))

        return message

    def redirectURL(self, realm, return_to=None, immediate=False):
        """Returns a URL with an encoded OpenID request.

        The resulting URL is the OpenID provider's endpoint URL with
        parameters appended as query arguments.  You should redirect
        the user agent to this URL.

        OpenID 2.0 endpoints also accept POST requests, see
        C{L{shouldSendRedirect}} and C{L{formMarkup}}.

        @param realm: The URL (or URL pattern) that identifies your
            web site to the user when she is authorizing it.

        @type realm: str

        @param return_to: The URL that the OpenID provider will send the
            user back to after attempting to verify her identity.

            Not specifying a return_to URL means that the user will not
            be returned to the site issuing the request upon its
            completion.

        @type return_to: str

        @param immediate: If True, the OpenID provider is to send back
            a response immediately, useful for behind-the-scenes
            authentication attempts.  Otherwise the OpenID provider
            may engage the user before providing a response.  This is
            the default case, as the user may need to provide
            credentials or approve the request before a positive
            response can be sent.

        @type immediate: bool

        @returns: The URL to redirect the user agent to.

        @returntype: str
        """
        message = self.getMessage(realm, return_to, immediate)
        return message.toURL(self.endpoint.server_url)

    def formMarkup(self,
                   realm,
                   return_to=None,
                   immediate=False,
                   form_tag_attrs=None):
        """Get html for a form to submit this request to the IDP.

        @param form_tag_attrs: Dictionary of attributes to be added to
            the form tag. 'accept-charset' and 'enctype' have defaults
            that can be overridden. If a value is supplied for
            'action' or 'method', it will be replaced.
        @type form_tag_attrs: {unicode: unicode}
        """
        message = self.getMessage(realm, return_to, immediate)
        return message.toFormMarkup(self.endpoint.server_url, form_tag_attrs)

    def htmlMarkup(self,
                   realm,
                   return_to=None,
                   immediate=False,
                   form_tag_attrs=None):
        """Get an autosubmitting HTML page that submits this request to the
        IDP.  This is just a wrapper for formMarkup.

        @see: formMarkup

        @returns: str
        """
        return oidutil.autoSubmitHTML(
            self.formMarkup(realm, return_to, immediate, form_tag_attrs))

    def shouldSendRedirect(self):
        """Should this OpenID authentication request be sent as a HTTP
        redirect or as a POST (form submission)?

        @rtype: bool
        """
        return self.endpoint.compatibilityMode()


FAILURE = 'failure'
SUCCESS = 'success'
CANCEL = 'cancel'
SETUP_NEEDED = 'setup_needed'


class Response(object):
    status = None

    def setEndpoint(self, endpoint):
        self.endpoint = endpoint
        if endpoint is None:
            self.identity_url = None
        else:
            self.identity_url = endpoint.claimed_id

    def getDisplayIdentifier(self):
        """Return the display identifier for this response.

        The display identifier is related to the Claimed Identifier, but the
        two are not always identical.  The display identifier is something the
        user should recognize as what they entered, whereas the response's
        claimed identifier (in the L{identity_url} attribute) may have extra
        information for better persistence.

        URLs will be stripped of their fragments for display.  XRIs will
        display the human-readable identifier (i-name) instead of the
        persistent identifier (i-number).

        Use the display identifier in your user interface.  Use
        L{identity_url} for querying your database or authorization server.
        """
        if self.endpoint is not None:
            return self.endpoint.getDisplayIdentifier()
        return None


class SuccessResponse(Response):
    """A response with a status of SUCCESS. Indicates that this request is a
    successful acknowledgement from the OpenID server that the
    supplied URL is, indeed controlled by the requesting agent.

    @ivar identity_url: The identity URL that has been authenticated;
          the Claimed Identifier.
        See also L{getDisplayIdentifier}.

    @ivar endpoint: The endpoint that authenticated the identifier.  You
        may access other discovered information related to this endpoint,
        such as the CanonicalID of an XRI, through this object.
    @type endpoint:
       L{OpenIDServiceEndpoint<openid.consumer.discover.OpenIDServiceEndpoint>}

    @ivar signed_fields: The arguments in the server's response that
        were signed and verified.

    @cvar status: SUCCESS
    """

    status = SUCCESS

    def __init__(self, endpoint, message, signed_fields=None):
        # Don't use setEndpoint, because endpoint should never be None
        # for a successfull transaction.
        self.endpoint = endpoint
        self.identity_url = endpoint.claimed_id

        self.message = message

        if signed_fields is None:
            signed_fields = []
        self.signed_fields = signed_fields

    def isOpenID1(self):
        """Was this authentication response an OpenID 1 authentication
        response?
        """
        return self.message.isOpenID1()

    def isSigned(self, ns_uri, ns_key):
        """Return whether a particular key is signed, regardless of
        its namespace alias
        """
        return self.message.getKey(ns_uri, ns_key) in self.signed_fields

    def getSigned(self, ns_uri, ns_key, default=None):
        """Return the specified signed field if available,
        otherwise return default
        """
        if self.isSigned(ns_uri, ns_key):
            return self.message.getArg(ns_uri, ns_key, default)
        else:
            return default

    def getSignedNS(self, ns_uri):
        """Get signed arguments from the response message.  Return a
        dict of all arguments in the specified namespace.  If any of
        the arguments are not signed, return None.
        """
        msg_args = self.message.getArgs(ns_uri)

        for key in msg_args.keys():
            if not self.isSigned(ns_uri, key):
                logging.info(
                    "SuccessResponse.getSignedNS: (%s, %s) not signed." %
                    (ns_uri, key))
                return None

        return msg_args

    def extensionResponse(self, namespace_uri, require_signed):
        """Return response arguments in the specified namespace.

        @param namespace_uri: The namespace URI of the arguments to be
        returned.

        @param require_signed: True if the arguments should be among
        those signed in the response, False if you don't care.

        If require_signed is True and the arguments are not signed,
        return None.
        """
        if require_signed:
            return self.getSignedNS(namespace_uri)
        else:
            return self.message.getArgs(namespace_uri)

    def getReturnTo(self):
        """Get the openid.return_to argument from this response.

        This is useful for verifying that this request was initiated
        by this consumer.

        @returns: The return_to URL supplied to the server on the
            initial request, or C{None} if the response did not contain
            an C{openid.return_to} argument.

        @returntype: str
        """
        return self.getSigned(OPENID_NS, 'return_to')

    def __eq__(self, other):
        return ((self.endpoint == other.endpoint) and
                (self.identity_url == other.identity_url) and
                (self.message == other.message) and
                (self.signed_fields == other.signed_fields) and
                (self.status == other.status))

    def __ne__(self, other):
        return not (self == other)

    def __repr__(self):
        return '<%s.%s id=%r signed=%r>' % (
            self.__class__.__module__, self.__class__.__name__,
            self.identity_url, self.signed_fields)


class FailureResponse(Response):
    """A response with a status of FAILURE. Indicates that the OpenID
    protocol has failed. This could be locally or remotely triggered.

    @ivar identity_url:  The identity URL for which authenitcation was
        attempted, if it can be determined. Otherwise, None.

    @ivar message: A message indicating why the request failed, if one
        is supplied. otherwise, None.

    @cvar status: FAILURE
    """

    status = FAILURE

    def __init__(self, endpoint, message=None, contact=None, reference=None):
        self.setEndpoint(endpoint)
        self.message = message
        self.contact = contact
        self.reference = reference

    def __repr__(self):
        return "<%s.%s id=%r message=%r>" % (self.__class__.__module__,
                                             self.__class__.__name__,
                                             self.identity_url, self.message)


class CancelResponse(Response):
    """A response with a status of CANCEL. Indicates that the user
    cancelled the OpenID authentication request.

    @ivar identity_url: The identity URL for which authenitcation was
        attempted, if it can be determined. Otherwise, None.

    @cvar status: CANCEL
    """

    status = CANCEL

    def __init__(self, endpoint):
        self.setEndpoint(endpoint)


class SetupNeededResponse(Response):
    """A response with a status of SETUP_NEEDED. Indicates that the
    request was in immediate mode, and the server is unable to
    authenticate the user without further interaction.

    @ivar identity_url:  The identity URL for which authenitcation was
        attempted.

    @ivar setup_url: A URL that can be used to send the user to the
        server to set up for authentication. The user should be
        redirected in to the setup_url, either in the current window
        or in a new browser window.  C{None} in OpenID 2.0.

    @cvar status: SETUP_NEEDED
    """

    status = SETUP_NEEDED

    def __init__(self, endpoint, setup_url=None):
        self.setEndpoint(endpoint)
        self.setup_url = setup_url
