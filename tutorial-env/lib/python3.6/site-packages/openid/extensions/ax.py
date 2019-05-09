# -*- test-case-name: openid.test.test_ax -*-
"""Implements the OpenID Attribute Exchange specification, version 1.0.

@since: 2.1.0
"""

__all__ = [
    'AttributeRequest',
    'FetchRequest',
    'FetchResponse',
    'StoreRequest',
    'StoreResponse',
]

from openid import extension
from openid.server.trustroot import TrustRoot
from openid.message import NamespaceMap, OPENID_NS

# Use this as the 'count' value for an attribute in a FetchRequest to
# ask for as many values as the OP can provide.
UNLIMITED_VALUES = "unlimited"

# Minimum supported alias length in characters.  Here for
# completeness.
MINIMUM_SUPPORTED_ALIAS_LENGTH = 32


def checkAlias(alias):
    """
    Check an alias for invalid characters; raise AXError if any are
    found.  Return None if the alias is valid.
    """
    if ',' in alias:
        raise AXError("Alias %r must not contain comma" % (alias, ))
    if '.' in alias:
        raise AXError("Alias %r must not contain period" % (alias, ))


class AXError(ValueError):
    """Results from data that does not meet the attribute exchange 1.0
    specification"""


class NotAXMessage(AXError):
    """Raised when there is no Attribute Exchange mode in the message."""

    def __repr__(self):
        return self.__class__.__name__

    def __str__(self):
        return self.__class__.__name__


class AXMessage(extension.Extension):
    """Abstract class containing common code for attribute exchange messages

    @cvar ns_alias: The preferred namespace alias for attribute
        exchange messages

    @cvar mode: The type of this attribute exchange message. This must
        be overridden in subclasses.
    """

    # This class is abstract, so it's OK that it doesn't override the
    # abstract method in Extension:
    #
    #pylint:disable-msg=W0223

    ns_alias = 'ax'
    ns_uri = 'http://openid.net/srv/ax/1.0'
    mode = None  # NOTE mode is only ever set to a str value, see below

    def _checkMode(self, ax_args):
        """Raise an exception if the mode in the attribute exchange
        arguments does not match what is expected for this class.

        @raises NotAXMessage: When there is no mode value in ax_args at all.

        @raises AXError: When mode does not match.
        """
        mode = ax_args.get('mode')
        if isinstance(mode, bytes):
            mode = str(mode, encoding="utf-8")
        if mode != self.mode:
            if not mode:
                raise NotAXMessage()
            else:
                raise AXError('Expected mode %r; got %r' % (self.mode, mode))

    def _newArgs(self):
        """Return a set of attribute exchange arguments containing the
        basic information that must be in every attribute exchange
        message.
        """
        return {'mode': self.mode}


class AttrInfo(object):
    """Represents a single attribute in an attribute exchange
    request. This should be added to an AXRequest object in order to
    request the attribute.

    @ivar required: Whether the attribute will be marked as required
        when presented to the subject of the attribute exchange
        request.
    @type required: bool

    @ivar count: How many values of this type to request from the
        subject. Defaults to one.
    @type count: int

    @ivar type_uri: The identifier that determines what the attribute
        represents and how it is serialized. For example, one type URI
        representing dates could represent a Unix timestamp in base 10
        and another could represent a human-readable string.
    @type type_uri: str

    @ivar alias: The name that should be given to this alias in the
        request. If it is not supplied, a generic name will be
        assigned. For example, if you want to call a Unix timestamp
        value 'tstamp', set its alias to that value. If two attributes
        in the same message request to use the same alias, the request
        will fail to be generated.
    @type alias: str or NoneType
    """

    # It's OK that this class doesn't have public methods (it's just a
    # holder for a bunch of attributes):
    #
    #pylint:disable-msg=R0903

    def __init__(self, type_uri, count=1, required=False, alias=None):
        self.required = required
        self.count = count
        self.type_uri = type_uri
        self.alias = alias

        if self.alias is not None:
            checkAlias(self.alias)

    def wantsUnlimitedValues(self):
        """
        When processing a request for this attribute, the OP should
        call this method to determine whether all available attribute
        values were requested.  If self.count == UNLIMITED_VALUES,
        this returns True.  Otherwise this returns False, in which
        case self.count is an integer.
        """
        return self.count == UNLIMITED_VALUES


def toTypeURIs(namespace_map, alias_list_s):
    """Given a namespace mapping and a string containing a
    comma-separated list of namespace aliases, return a list of type
    URIs that correspond to those aliases.

    @param namespace_map: The mapping from namespace URI to alias
    @type namespace_map: openid.message.NamespaceMap

    @param alias_list_s: The string containing the comma-separated
        list of aliases. May also be None for convenience.
    @type alias_list_s: str or NoneType

    @returns: The list of namespace URIs that corresponds to the
        supplied list of aliases. If the string was zero-length or
        None, an empty list will be returned.

    @raise KeyError: If an alias is present in the list of aliases but
        is not present in the namespace map.
    """
    uris = []

    if alias_list_s:
        for alias in alias_list_s.split(','):
            type_uri = namespace_map.getNamespaceURI(alias)
            if type_uri is None:
                raise KeyError('No type is defined for attribute name %r' %
                               (alias, ))
            else:
                uris.append(type_uri)

    return uris


class FetchRequest(AXMessage):
    """An attribute exchange 'fetch_request' message. This message is
    sent by a relying party when it wishes to obtain attributes about
    the subject of an OpenID authentication request.

    @ivar requested_attributes: The attributes that have been
        requested thus far, indexed by the type URI.
    @type requested_attributes: {str:AttrInfo}

    @ivar update_url: A URL that will accept responses for this
        attribute exchange request, even in the absence of the user
        who made this request.
    """
    mode = 'fetch_request'

    def __init__(self, update_url=None):
        AXMessage.__init__(self)
        self.requested_attributes = {}
        self.update_url = update_url

    def add(self, attribute):
        """Add an attribute to this attribute exchange request.

        @param attribute: The attribute that is being requested
        @type attribute: C{L{AttrInfo}}

        @returns: None

        @raise KeyError: when the requested attribute is already
            present in this fetch request.
        """
        if attribute.type_uri in self.requested_attributes:
            raise KeyError('The attribute %r has already been requested' %
                           (attribute.type_uri, ))

        self.requested_attributes[attribute.type_uri] = attribute

    def getExtensionArgs(self):
        """Get the serialized form of this attribute fetch request.

        @returns: The fetch request message parameters
        @rtype: {unicode:unicode}
        """
        aliases = NamespaceMap()

        required = []
        if_available = []

        ax_args = self._newArgs()

        for type_uri, attribute in self.requested_attributes.items():
            if attribute.alias is None:
                alias = aliases.add(type_uri)
            else:
                # This will raise an exception when the second
                # attribute with the same alias is added. I think it
                # would be better to complain at the time that the
                # attribute is added to this object so that the code
                # that is adding it is identified in the stack trace,
                # but it's more work to do so, and it won't be 100%
                # accurate anyway, since the attributes are
                # mutable. So for now, just live with the fact that
                # we'll learn about the error later.
                #
                # The other possible approach is to hide the error and
                # generate a new alias on the fly. I think that would
                # probably be bad.
                alias = aliases.addAlias(type_uri, attribute.alias)

            if attribute.required:
                required.append(alias)
            else:
                if_available.append(alias)

            if attribute.count != 1:
                ax_args['count.' + alias] = str(attribute.count)

            ax_args['type.' + alias] = type_uri

        if required:
            ax_args['required'] = ','.join(required)

        if if_available:
            ax_args['if_available'] = ','.join(if_available)

        return ax_args

    def getRequiredAttrs(self):
        """Get the type URIs for all attributes that have been marked
        as required.

        @returns: A list of the type URIs for attributes that have
            been marked as required.
        @rtype: [str]
        """
        required = []
        for type_uri, attribute in self.requested_attributes.items():
            if attribute.required:
                required.append(type_uri)

        return required

    def fromOpenIDRequest(cls, openid_request):
        """Extract a FetchRequest from an OpenID message

        @param openid_request: The OpenID authentication request
            containing the attribute fetch request
        @type openid_request: C{L{openid.server.server.CheckIDRequest}}

        @rtype: C{L{FetchRequest}} or C{None}
        @returns: The FetchRequest extracted from the message or None, if
            the message contained no AX extension.

        @raises KeyError: if the AuthRequest is not consistent in its use
            of namespace aliases.

        @raises AXError: When parseExtensionArgs would raise same.

        @see: L{parseExtensionArgs}
        """
        message = openid_request.message
        ax_args = message.getArgs(cls.ns_uri)
        self = cls()
        try:
            self.parseExtensionArgs(ax_args)
        except NotAXMessage as err:
            return None

        if self.update_url:
            # Update URL must match the openid.realm of the underlying
            # OpenID 2 message.
            realm = message.getArg(OPENID_NS, 'realm',
                                   message.getArg(OPENID_NS, 'return_to'))

            if not realm:
                raise AXError(
                    ("Cannot validate update_url %r " + "against absent realm")
                    % (self.update_url, ))

            tr = TrustRoot.parse(realm)
            if not tr.validateURL(self.update_url):
                raise AXError(
                    "Update URL %r failed validation against realm %r" %
                    (self.update_url, realm, ))

        return self

    fromOpenIDRequest = classmethod(fromOpenIDRequest)

    def parseExtensionArgs(self, ax_args):
        """Given attribute exchange arguments, populate this FetchRequest.

        @param ax_args: Attribute Exchange arguments from the request.
            As returned from L{Message.getArgs<openid.message.Message.getArgs>}.
        @type ax_args: dict

        @raises KeyError: if the message is not consistent in its use
            of namespace aliases.

        @raises NotAXMessage: If ax_args does not include an Attribute Exchange
            mode.

        @raises AXError: If the data to be parsed does not follow the
            attribute exchange specification. At least when
            'if_available' or 'required' is not specified for a
            particular attribute type.
        """
        # Raises an exception if the mode is not the expected value
        self._checkMode(ax_args)

        aliases = NamespaceMap()

        for key, value in ax_args.items():
            if key.startswith('type.'):
                alias = key[5:]
                type_uri = value
                aliases.addAlias(type_uri, alias)

                count_key = 'count.' + alias
                count_s = ax_args.get(count_key)
                if count_s:
                    try:
                        count = int(count_s)
                        if count <= 0:
                            raise AXError(
                                "Count %r must be greater than zero, got %r" %
                                (count_key, count_s, ))
                    except ValueError:
                        if count_s != UNLIMITED_VALUES:
                            raise AXError("Invalid count value for %r: %r" %
                                          (count_key, count_s, ))
                        count = count_s
                else:
                    count = 1

                self.add(AttrInfo(type_uri, alias=alias, count=count))

        required = toTypeURIs(aliases, ax_args.get('required'))

        for type_uri in required:
            self.requested_attributes[type_uri].required = True

        if_available = toTypeURIs(aliases, ax_args.get('if_available'))

        all_type_uris = required + if_available

        for type_uri in aliases.iterNamespaceURIs():
            if type_uri not in all_type_uris:
                raise AXError('Type URI %r was in the request but not '
                              'present in "required" or "if_available"' %
                              (type_uri, ))

        self.update_url = ax_args.get('update_url')

    def iterAttrs(self):
        """Iterate over the AttrInfo objects that are
        contained in this fetch_request.
        """
        return iter(self.requested_attributes.values())

    def __iter__(self):
        """Iterate over the attribute type URIs in this fetch_request
        """
        return iter(self.requested_attributes)

    def has_key(self, type_uri):
        """Is the given type URI present in this fetch_request?
        """
        return type_uri in self.requested_attributes

    __contains__ = has_key


class AXKeyValueMessage(AXMessage):
    """An abstract class that implements a message that has attribute
    keys and values. It contains the common code between
    fetch_response and store_request.
    """

    # This class is abstract, so it's OK that it doesn't override the
    # abstract method in Extension:
    #
    #pylint:disable-msg=W0223

    def __init__(self):
        AXMessage.__init__(self)
        self.data = {}

    def addValue(self, type_uri, value):
        """Add a single value for the given attribute type to the
        message. If there are already values specified for this type,
        this value will be sent in addition to the values already
        specified.

        @param type_uri: The URI for the attribute

        @param value: The value to add to the response to the relying
            party for this attribute
        @type value: unicode

        @returns: None
        """
        try:
            values = self.data[type_uri]
        except KeyError:
            values = self.data[type_uri] = []

        values.append(value)

    def setValues(self, type_uri, values):
        """Set the values for the given attribute type. This replaces
        any values that have already been set for this attribute.

        @param type_uri: The URI for the attribute

        @param values: A list of values to send for this attribute.
        @type values: [unicode]
        """

        self.data[type_uri] = values

    def _getExtensionKVArgs(self, aliases=None):
        """Get the extension arguments for the key/value pairs
        contained in this message.

        @param aliases: An alias mapping. Set to None if you don't
            care about the aliases for this request.
        """
        if aliases is None:
            aliases = NamespaceMap()

        ax_args = {}

        for type_uri, values in self.data.items():
            alias = aliases.add(type_uri)

            ax_args['type.' + alias] = type_uri
            ax_args['count.' + alias] = str(len(values))

            for i, value in enumerate(values):
                key = 'value.%s.%d' % (alias, i + 1)
                ax_args[key] = value

        return ax_args

    def parseExtensionArgs(self, ax_args):
        """Parse attribute exchange key/value arguments into this
        object.

        @param ax_args: The attribute exchange fetch_response
            arguments, with namespacing removed.
        @type ax_args: {unicode:unicode}

        @returns: None

        @raises ValueError: If the message has bad values for
            particular fields

        @raises KeyError: If the namespace mapping is bad or required
            arguments are missing
        """
        self._checkMode(ax_args)

        aliases = NamespaceMap()

        for key, value in ax_args.items():
            if key.startswith('type.'):
                type_uri = value
                alias = key[5:]
                checkAlias(alias)
                aliases.addAlias(type_uri, alias)

        for type_uri, alias in aliases.items():
            try:
                count_s = ax_args['count.' + alias]
            except KeyError:
                value = ax_args['value.' + alias]

                if value == '':
                    values = []
                else:
                    values = [value]
            else:
                count = int(count_s)
                values = []
                for i in range(1, count + 1):
                    value_key = 'value.%s.%d' % (alias, i)
                    value = ax_args[value_key]
                    values.append(value)

            self.data[type_uri] = values

    def getSingle(self, type_uri, default=None):
        """Get a single value for an attribute. If no value was sent
        for this attribute, use the supplied default. If there is more
        than one value for this attribute, this method will fail.

        @type type_uri: str
        @param type_uri: The URI for the attribute

        @param default: The value to return if the attribute was not
            sent in the fetch_response.

        @returns: The value of the attribute in the fetch_response
            message, or the default supplied
        @rtype: unicode or NoneType

        @raises ValueError: If there is more than one value for this
            parameter in the fetch_response message.
        @raises KeyError: If the attribute was not sent in this response
        """
        values = self.data.get(type_uri)
        if not values:
            return default
        elif len(values) == 1:
            return values[0]
        else:
            raise AXError('More than one value present for %r' % (type_uri, ))

    def get(self, type_uri):
        """Get the list of values for this attribute in the
        fetch_response.

        XXX: what to do if the values are not present? default
        parameter? this is funny because it's always supposed to
        return a list, so the default may break that, though it's
        provided by the user's code, so it might be okay. If no
        default is supplied, should the return be None or []?

        @param type_uri: The URI of the attribute

        @returns: The list of values for this attribute in the
            response. May be an empty list.
        @rtype: [unicode]

        @raises KeyError: If the attribute was not sent in the response
        """
        return self.data[type_uri]

    def count(self, type_uri):
        """Get the number of responses for a particular attribute in
        this fetch_response message.

        @param type_uri: The URI of the attribute

        @returns: The number of values sent for this attribute

        @raises KeyError: If the attribute was not sent in the
            response. KeyError will not be raised if the number of
            values was zero.
        """
        return len(self.get(type_uri))


class FetchResponse(AXKeyValueMessage):
    """A fetch_response attribute exchange message
    """
    mode = 'fetch_response'

    def __init__(self, request=None, update_url=None):
        """
        @param request: When supplied, I will use namespace aliases
            that match those in this request.  I will also check to
            make sure I do not respond with attributes that were not
            requested.

        @type request: L{FetchRequest}

        @param update_url: By default, C{update_url} is taken from the
            request.  But if you do not supply the request, you may set
            the C{update_url} here.

        @type update_url: str
        """
        AXKeyValueMessage.__init__(self)
        self.update_url = update_url
        self.request = request

    def getExtensionArgs(self):
        """Serialize this object into arguments in the attribute
        exchange namespace

        @returns: The dictionary of unqualified attribute exchange
            arguments that represent this fetch_response.
        @rtype: {unicode;unicode}
        """

        aliases = NamespaceMap()

        zero_value_types = []

        if self.request is not None:
            # Validate the data in the context of the request (the
            # same attributes should be present in each, and the
            # counts in the response must be no more than the counts
            # in the request)

            for type_uri in self.data:
                if type_uri not in self.request:
                    raise KeyError(
                        'Response attribute not present in request: %r' %
                        (type_uri, ))

            for attr_info in self.request.iterAttrs():
                # Copy the aliases from the request so that reading
                # the response in light of the request is easier
                if attr_info.alias is None:
                    aliases.add(attr_info.type_uri)
                else:
                    aliases.addAlias(attr_info.type_uri, attr_info.alias)

                try:
                    values = self.data[attr_info.type_uri]
                except KeyError:
                    values = []
                    zero_value_types.append(attr_info)

                if (attr_info.count != UNLIMITED_VALUES) and \
                       (attr_info.count < len(values)):
                    raise AXError(
                        'More than the number of requested values were '
                        'specified for %r' % (attr_info.type_uri, ))

        kv_args = self._getExtensionKVArgs(aliases)

        # Add the KV args into the response with the args that are
        # unique to the fetch_response
        ax_args = self._newArgs()

        # For each requested attribute, put its type/alias and count
        # into the response even if no data were returned.
        for attr_info in zero_value_types:
            alias = aliases.getAlias(attr_info.type_uri)
            kv_args['type.' + alias] = attr_info.type_uri
            kv_args['count.' + alias] = '0'

        update_url = ((self.request and self.request.update_url) or
                      self.update_url)

        if update_url:
            ax_args['update_url'] = update_url

        ax_args.update(kv_args)

        return ax_args

    def parseExtensionArgs(self, ax_args):
        """@see: {Extension.parseExtensionArgs<openid.extension.Extension.parseExtensionArgs>}"""
        super(FetchResponse, self).parseExtensionArgs(ax_args)
        self.update_url = ax_args.get('update_url')

    def fromSuccessResponse(cls, success_response, signed=True):
        """Construct a FetchResponse object from an OpenID library
        SuccessResponse object.

        @param success_response: A successful id_res response object
        @type success_response: openid.consumer.consumer.SuccessResponse

        @param signed: Whether non-signed args should be
            processsed. If True (the default), only signed arguments
            will be processsed.
        @type signed: bool

        @returns: A FetchResponse containing the data from the OpenID
            message, or None if the SuccessResponse did not contain AX
            extension data.

        @raises AXError: when the AX data cannot be parsed.
        """
        self = cls()
        ax_args = success_response.extensionResponse(self.ns_uri, signed)

        try:
            self.parseExtensionArgs(ax_args)
        except NotAXMessage as err:
            return None
        else:
            return self

    fromSuccessResponse = classmethod(fromSuccessResponse)


class StoreRequest(AXKeyValueMessage):
    """A store request attribute exchange message representation
    """
    mode = 'store_request'

    def __init__(self, aliases=None):
        """
        @param aliases: The namespace aliases to use when making this
            store request.  Leave as None to use defaults.
        """
        super(StoreRequest, self).__init__()
        self.aliases = aliases

    def getExtensionArgs(self):
        """
        @see: L{Extension.getExtensionArgs<openid.extension.Extension.getExtensionArgs>}
        """
        ax_args = self._newArgs()
        kv_args = self._getExtensionKVArgs(self.aliases)
        ax_args.update(kv_args)
        return ax_args


class StoreResponse(AXMessage):
    """An indication that the store request was processed along with
    this OpenID transaction.
    """

    SUCCESS_MODE = 'store_response_success'
    FAILURE_MODE = 'store_response_failure'

    def __init__(self, succeeded=True, error_message=None):
        AXMessage.__init__(self)

        if succeeded and error_message is not None:
            raise AXError('An error message may only be included in a '
                          'failing fetch response')
        if succeeded:
            self.mode = self.SUCCESS_MODE
        else:
            self.mode = self.FAILURE_MODE

        self.error_message = error_message

    def succeeded(self):
        """Was this response a success response?"""
        return self.mode == self.SUCCESS_MODE

    def getExtensionArgs(self):
        """@see: {Extension.getExtensionArgs<openid.extension.Extension.getExtensionArgs>}"""
        ax_args = self._newArgs()
        if not self.succeeded() and self.error_message:
            ax_args['error'] = self.error_message

        return ax_args
