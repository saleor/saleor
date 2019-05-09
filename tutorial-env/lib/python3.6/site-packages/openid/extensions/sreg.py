"""Simple registration request and response parsing and object representation

This module contains objects representing simple registration requests
and responses that can be used with both OpenID relying parties and
OpenID providers.

  1. The relying party creates a request object and adds it to the
     C{L{AuthRequest<openid.consumer.consumer.AuthRequest>}} object
     before making the C{checkid_} request to the OpenID provider::

      auth_request.addExtension(SRegRequest(required=['email']))

  2. The OpenID provider extracts the simple registration request from
     the OpenID request using C{L{SRegRequest.fromOpenIDRequest}},
     gets the user's approval and data, creates a C{L{SRegResponse}}
     object and adds it to the C{id_res} response::

      sreg_req = SRegRequest.fromOpenIDRequest(checkid_request)
      # [ get the user's approval and data, informing the user that
      #   the fields in sreg_response were requested ]
      sreg_resp = SRegResponse.extractResponse(sreg_req, user_data)
      sreg_resp.toMessage(openid_response.fields)

  3. The relying party uses C{L{SRegResponse.fromSuccessResponse}} to
     extract the data from the OpenID response::

      sreg_resp = SRegResponse.fromSuccessResponse(success_response)

@since: 2.0

@var sreg_data_fields: The names of the data fields that are listed in
    the sreg spec, and a description of them in English

@var sreg_uri: The preferred URI to use for the simple registration
    namespace and XRD Type value
"""

from openid.message import registerNamespaceAlias, \
     NamespaceAliasRegistrationError
from openid.extension import Extension
import logging

try:
    str  #pylint:disable-msg=W0104
except NameError:
    # For Python 2.2
    str = (str, str)  #pylint:disable-msg=W0622

__all__ = [
    'SRegRequest',
    'SRegResponse',
    'data_fields',
    'ns_uri',
    'ns_uri_1_0',
    'ns_uri_1_1',
    'supportsSReg',
]

# The data fields that are listed in the sreg spec
data_fields = {
    'fullname': 'Full Name',
    'nickname': 'Nickname',
    'dob': 'Date of Birth',
    'email': 'E-mail Address',
    'gender': 'Gender',
    'postcode': 'Postal Code',
    'country': 'Country',
    'language': 'Language',
    'timezone': 'Time Zone',
}


def checkFieldName(field_name):
    """Check to see that the given value is a valid simple
    registration data field name.

    @raise ValueError: if the field name is not a valid simple
        registration data field name
    """
    if field_name not in data_fields:
        raise ValueError('%r is not a defined simple registration field' %
                         (field_name, ))


# URI used in the wild for Yadis documents advertising simple
# registration support
ns_uri_1_0 = 'http://openid.net/sreg/1.0'

# URI in the draft specification for simple registration 1.1
# <http://openid.net/specs/openid-simple-registration-extension-1_1-01.html>
ns_uri_1_1 = 'http://openid.net/extensions/sreg/1.1'

# This attribute will always hold the preferred URI to use when adding
# sreg support to an XRDS file or in an OpenID namespace declaration.
ns_uri = ns_uri_1_1

try:
    registerNamespaceAlias(ns_uri_1_1, 'sreg')
except NamespaceAliasRegistrationError as e:
    logging.exception('registerNamespaceAlias(%r, %r) failed: %s' %
                      (ns_uri_1_1, 'sreg', str(e), ))


def supportsSReg(endpoint):
    """Does the given endpoint advertise support for simple
    registration?

    @param endpoint: The endpoint object as returned by OpenID discovery
    @type endpoint: openid.consumer.discover.OpenIDEndpoint

    @returns: Whether an sreg type was advertised by the endpoint
    @rtype: bool
    """
    return (endpoint.usesExtension(ns_uri_1_1) or
            endpoint.usesExtension(ns_uri_1_0))


class SRegNamespaceError(ValueError):
    """The simple registration namespace was not found and could not
    be created using the expected name (there's another extension
    using the name 'sreg')

    This is not I{illegal}, for OpenID 2, although it probably
    indicates a problem, since it's not expected that other extensions
    will re-use the alias that is in use for OpenID 1.

    If this is an OpenID 1 request, then there is no recourse. This
    should not happen unless some code has modified the namespaces for
    the message that is being processed.
    """


def getSRegNS(message):
    """Extract the simple registration namespace URI from the given
    OpenID message. Handles OpenID 1 and 2, as well as both sreg
    namespace URIs found in the wild, as well as missing namespace
    definitions (for OpenID 1)

    @param message: The OpenID message from which to parse simple
        registration fields. This may be a request or response message.
    @type message: C{L{openid.message.Message}}

    @returns: the sreg namespace URI for the supplied message. The
        message may be modified to define a simple registration
        namespace.
    @rtype: C{str}

    @raise ValueError: when using OpenID 1 if the message defines
        the 'sreg' alias to be something other than a simple
        registration type.
    """
    # See if there exists an alias for one of the two defined simple
    # registration types.
    for sreg_ns_uri in [ns_uri_1_1, ns_uri_1_0]:
        alias = message.namespaces.getAlias(sreg_ns_uri)
        if alias is not None:
            break
    else:
        # There is no alias for either of the types, so try to add
        # one. We default to using the modern value (1.1)
        sreg_ns_uri = ns_uri_1_1
        try:
            message.namespaces.addAlias(ns_uri_1_1, 'sreg')
        except KeyError as why:
            # An alias for the string 'sreg' already exists, but it's
            # defined for something other than simple registration
            raise SRegNamespaceError(why)

    # we know that sreg_ns_uri defined, because it's defined in the
    # else clause of the loop as well, so disable the warning
    return sreg_ns_uri  #pylint:disable-msg=W0631


class SRegRequest(Extension):
    """An object to hold the state of a simple registration request.

    @ivar required: A list of the required fields in this simple
        registration request
    @type required: [str]

    @ivar optional: A list of the optional fields in this simple
        registration request
    @type optional: [str]

    @ivar policy_url: The policy URL that was provided with the request
    @type policy_url: str or NoneType

    @group Consumer: requestField, requestFields, getExtensionArgs, addToOpenIDRequest
    @group Server: fromOpenIDRequest, parseExtensionArgs
    """

    ns_alias = 'sreg'

    def __init__(self,
                 required=None,
                 optional=None,
                 policy_url=None,
                 sreg_ns_uri=ns_uri):
        """Initialize an empty simple registration request"""
        Extension.__init__(self)
        self.required = []
        self.optional = []
        self.policy_url = policy_url
        self.ns_uri = sreg_ns_uri

        if required:
            self.requestFields(required, required=True, strict=True)

        if optional:
            self.requestFields(optional, required=False, strict=True)

    # Assign getSRegNS to a static method so that it can be
    # overridden for testing.
    _getSRegNS = staticmethod(getSRegNS)

    def fromOpenIDRequest(cls, request):
        """Create a simple registration request that contains the
        fields that were requested in the OpenID request with the
        given arguments

        @param request: The OpenID request
        @type request: openid.server.CheckIDRequest

        @returns: The newly created simple registration request
        @rtype: C{L{SRegRequest}}
        """
        self = cls()

        # Since we're going to mess with namespace URI mapping, don't
        # mutate the object that was passed in.
        message = request.message.copy()

        self.ns_uri = self._getSRegNS(message)
        args = message.getArgs(self.ns_uri)
        self.parseExtensionArgs(args)

        return self

    fromOpenIDRequest = classmethod(fromOpenIDRequest)

    def parseExtensionArgs(self, args, strict=False):
        """Parse the unqualified simple registration request
        parameters and add them to this object.

        This method is essentially the inverse of
        C{L{getExtensionArgs}}. This method restores the serialized simple
        registration request fields.

        If you are extracting arguments from a standard OpenID
        checkid_* request, you probably want to use C{L{fromOpenIDRequest}},
        which will extract the sreg namespace and arguments from the
        OpenID request. This method is intended for cases where the
        OpenID server needs more control over how the arguments are
        parsed than that method provides.

        >>> args = message.getArgs(ns_uri)
        >>> request.parseExtensionArgs(args)

        @param args: The unqualified simple registration arguments
        @type args: {str:str}

        @param strict: Whether requests with fields that are not
            defined in the simple registration specification should be
            tolerated (and ignored)
        @type strict: bool

        @returns: None; updates this object
        """
        for list_name in ['required', 'optional']:
            required = (list_name == 'required')
            items = args.get(list_name)
            if items:
                for field_name in items.split(','):
                    try:
                        self.requestField(field_name, required, strict)
                    except ValueError:
                        if strict:
                            raise

        self.policy_url = args.get('policy_url')

    def allRequestedFields(self):
        """A list of all of the simple registration fields that were
        requested, whether they were required or optional.

        @rtype: [str]
        """
        return self.required + self.optional

    def wereFieldsRequested(self):
        """Have any simple registration fields been requested?

        @rtype: bool
        """
        return bool(self.allRequestedFields())

    def __contains__(self, field_name):
        """Was this field in the request?"""
        return (field_name in self.required or field_name in self.optional)

    def requestField(self, field_name, required=False, strict=False):
        """Request the specified field from the OpenID user

        @param field_name: the unqualified simple registration field name
        @type field_name: str

        @param required: whether the given field should be presented
            to the user as being a required to successfully complete
            the request

        @param strict: whether to raise an exception when a field is
            added to a request more than once

        @raise ValueError: when the field requested is not a simple
            registration field or strict is set and the field was
            requested more than once
        """
        checkFieldName(field_name)

        if strict:
            if field_name in self.required or field_name in self.optional:
                raise ValueError('That field has already been requested')
        else:
            if field_name in self.required:
                return

            if field_name in self.optional:
                if required:
                    self.optional.remove(field_name)
                else:
                    return

        if required:
            self.required.append(field_name)
        else:
            self.optional.append(field_name)

    def requestFields(self, field_names, required=False, strict=False):
        """Add the given list of fields to the request

        @param field_names: The simple registration data fields to request
        @type field_names: [str]

        @param required: Whether these values should be presented to
            the user as required

        @param strict: whether to raise an exception when a field is
            added to a request more than once

        @raise ValueError: when a field requested is not a simple
            registration field or strict is set and a field was
            requested more than once
        """
        if isinstance(field_names, str):
            raise TypeError('Fields should be passed as a list of '
                            'strings (not %r)' % (type(field_names), ))

        for field_name in field_names:
            self.requestField(field_name, required, strict=strict)

    def getExtensionArgs(self):
        """Get a dictionary of unqualified simple registration
        arguments representing this request.

        This method is essentially the inverse of
        C{L{parseExtensionArgs}}. This method serializes the simple
        registration request fields.

        @rtype: {str:str}
        """
        args = {}

        if self.required:
            args['required'] = ','.join(self.required)

        if self.optional:
            args['optional'] = ','.join(self.optional)

        if self.policy_url:
            args['policy_url'] = self.policy_url

        return args


class SRegResponse(Extension):
    """Represents the data returned in a simple registration response
    inside of an OpenID C{id_res} response. This object will be
    created by the OpenID server, added to the C{id_res} response
    object, and then extracted from the C{id_res} message by the
    Consumer.

    @ivar data: The simple registration data, keyed by the unqualified
        simple registration name of the field (i.e. nickname is keyed
        by C{'nickname'})

    @ivar ns_uri: The URI under which the simple registration data was
        stored in the response message.

    @group Server: extractResponse
    @group Consumer: fromSuccessResponse
    @group Read-only dictionary interface: keys, iterkeys, items, iteritems,
        __iter__, get, __getitem__, keys, has_key
    """

    ns_alias = 'sreg'

    def __init__(self, data=None, sreg_ns_uri=ns_uri):
        Extension.__init__(self)
        if data is None:
            self.data = {}
        else:
            self.data = data

        self.ns_uri = sreg_ns_uri

    def extractResponse(cls, request, data):
        """Take a C{L{SRegRequest}} and a dictionary of simple
        registration values and create a C{L{SRegResponse}}
        object containing that data.

        @param request: The simple registration request object
        @type request: SRegRequest

        @param data: The simple registration data for this
            response, as a dictionary from unqualified simple
            registration field name to string (unicode) value. For
            instance, the nickname should be stored under the key
            'nickname'.
        @type data: {str:str}

        @returns: a simple registration response object
        @rtype: SRegResponse
        """
        self = cls()
        self.ns_uri = request.ns_uri
        for field in request.allRequestedFields():
            value = data.get(field)
            if value is not None:
                self.data[field] = value
        return self

    extractResponse = classmethod(extractResponse)

    # Assign getSRegArgs to a static method so that it can be
    # overridden for testing
    _getSRegNS = staticmethod(getSRegNS)

    def fromSuccessResponse(cls, success_response, signed_only=True):
        """Create a C{L{SRegResponse}} object from a successful OpenID
        library response
        (C{L{openid.consumer.consumer.SuccessResponse}}) response
        message

        @param success_response: A SuccessResponse from consumer.complete()
        @type success_response: C{L{openid.consumer.consumer.SuccessResponse}}

        @param signed_only: Whether to process only data that was
            signed in the id_res message from the server.
        @type signed_only: bool

        @rtype: SRegResponse
        @returns: A simple registration response containing the data
            that was supplied with the C{id_res} response.
        """
        self = cls()
        self.ns_uri = self._getSRegNS(success_response.message)
        if signed_only:
            args = success_response.getSignedNS(self.ns_uri)
        else:
            args = success_response.message.getArgs(self.ns_uri)

        if not args:
            return None

        for field_name in data_fields:
            if field_name in args:
                self.data[field_name] = args[field_name]

        return self

    fromSuccessResponse = classmethod(fromSuccessResponse)

    def getExtensionArgs(self):
        """Get the fields to put in the simple registration namespace
        when adding them to an id_res message.

        @see: openid.extension
        """
        return self.data

    # Read-only dictionary interface
    def get(self, field_name, default=None):
        """Like dict.get, except that it checks that the field name is
        defined by the simple registration specification"""
        checkFieldName(field_name)
        return self.data.get(field_name, default)

    def items(self):
        """All of the data values in this simple registration response
        """
        return list(self.data.items())

    def iteritems(self):
        return iter(self.data.items())

    def keys(self):
        return list(self.data.keys())

    def iterkeys(self):
        return iter(self.data.keys())

    def has_key(self, key):
        return key in self

    def __contains__(self, field_name):
        checkFieldName(field_name)
        return field_name in self.data

    def __iter__(self):
        return iter(self.data)

    def __getitem__(self, field_name):
        checkFieldName(field_name)
        return self.data[field_name]

    def __bool__(self):
        return bool(self.data)
