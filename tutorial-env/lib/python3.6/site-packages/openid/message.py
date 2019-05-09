"""Extension argument processing code
"""
__all__ = [
    'Message', 'NamespaceMap', 'no_default', 'registerNamespaceAlias',
    'OPENID_NS', 'BARE_NS', 'OPENID1_NS', 'OPENID2_NS', 'SREG_URI',
    'IDENTIFIER_SELECT'
]

import copy
import warnings
import urllib.request
import urllib.error

from openid import oidutil
from openid import kvform
try:
    ElementTree = oidutil.importElementTree()
except ImportError:
    # No elementtree found, so give up, but don't fail to import,
    # since we have fallbacks.
    ElementTree = None

# This doesn't REALLY belong here, but where is better?
IDENTIFIER_SELECT = 'http://specs.openid.net/auth/2.0/identifier_select'

# URI for Simple Registration extension, the only commonly deployed
# OpenID 1.x extension, and so a special case
SREG_URI = 'http://openid.net/sreg/1.0'

# The OpenID 1.X namespace URI
OPENID1_NS = 'http://openid.net/signon/1.0'
THE_OTHER_OPENID1_NS = 'http://openid.net/signon/1.1'

OPENID1_NAMESPACES = OPENID1_NS, THE_OTHER_OPENID1_NS

# The OpenID 2.0 namespace URI
OPENID2_NS = 'http://specs.openid.net/auth/2.0'

# The namespace consisting of pairs with keys that are prefixed with
# "openid."  but not in another namespace.
NULL_NAMESPACE = oidutil.Symbol('Null namespace')

# The null namespace, when it is an allowed OpenID namespace
OPENID_NS = oidutil.Symbol('OpenID namespace')

# The top-level namespace, excluding all pairs with keys that start
# with "openid."
BARE_NS = oidutil.Symbol('Bare namespace')

# Limit, in bytes, of identity provider and return_to URLs, including
# response payload.  See OpenID 1.1 specification, Appendix D.
OPENID1_URL_LIMIT = 2047

# All OpenID protocol fields.  Used to check namespace aliases.
OPENID_PROTOCOL_FIELDS = [
    'ns',
    'mode',
    'error',
    'return_to',
    'contact',
    'reference',
    'signed',
    'assoc_type',
    'session_type',
    'dh_modulus',
    'dh_gen',
    'dh_consumer_public',
    'claimed_id',
    'identity',
    'realm',
    'invalidate_handle',
    'op_endpoint',
    'response_nonce',
    'sig',
    'assoc_handle',
    'trust_root',
    'openid',
]


class UndefinedOpenIDNamespace(ValueError):
    """Raised if the generic OpenID namespace is accessed when there
    is no OpenID namespace set for this message."""


class InvalidOpenIDNamespace(ValueError):
    """Raised if openid.ns is not a recognized value.

    For recognized values, see L{Message.allowed_openid_namespaces}
    """

    def __str__(self):
        s = "Invalid OpenID Namespace"
        if self.args:
            s += " %r" % (self.args[0], )
        return s


# Sentinel used for Message implementation to indicate that getArg
# should raise an exception instead of returning a default.
no_default = object()

# Global namespace / alias registration map.  See
# registerNamespaceAlias.
registered_aliases = {}


class NamespaceAliasRegistrationError(Exception):
    """
    Raised when an alias or namespace URI has already been registered.
    """
    pass


def registerNamespaceAlias(namespace_uri, alias):
    """
    Registers a (namespace URI, alias) mapping in a global namespace
    alias map.  Raises NamespaceAliasRegistrationError if either the
    namespace URI or alias has already been registered with a
    different value.  This function is required if you want to use a
    namespace with an OpenID 1 message.
    """
    global registered_aliases

    if registered_aliases.get(alias) == namespace_uri:
        return

    if namespace_uri in list(registered_aliases.values()):
        raise NamespaceAliasRegistrationError(
            'Namespace uri %r already registered' % (namespace_uri, ))

    if alias in registered_aliases:
        raise NamespaceAliasRegistrationError('Alias %r already registered' %
                                              (alias, ))

    registered_aliases[alias] = namespace_uri


class Message(object):
    """
    In the implementation of this object, None represents the global
    namespace as well as a namespace with no key.

    @cvar namespaces: A dictionary specifying specific
        namespace-URI to alias mappings that should be used when
        generating namespace aliases.

    @ivar ns_args: two-level dictionary of the values in this message,
        grouped by namespace URI. The first level is the namespace
        URI.
    """

    allowed_openid_namespaces = [OPENID1_NS, THE_OTHER_OPENID1_NS, OPENID2_NS]

    def __init__(self, openid_namespace=None):
        """Create an empty Message.

        @raises InvalidOpenIDNamespace: if openid_namespace is not in
            L{Message.allowed_openid_namespaces}
        """
        self.args = {}
        self.namespaces = NamespaceMap()
        if openid_namespace is None:
            self._openid_ns_uri = None
        else:
            implicit = openid_namespace in OPENID1_NAMESPACES
            self.setOpenIDNamespace(openid_namespace, implicit)

    @classmethod
    def fromPostArgs(cls, args):
        """Construct a Message containing a set of POST arguments.

        """
        self = cls()

        # Partition into "openid." args and bare args
        openid_args = {}
        for key, value in args.items():
            if isinstance(value, list):
                raise TypeError("query dict must have one value for each key, "
                                "not lists of values.  Query is %r" % (args, ))

            try:
                prefix, rest = key.split('.', 1)
            except ValueError:
                prefix = None

            if prefix != 'openid':
                self.args[(BARE_NS, key)] = value
            else:
                openid_args[rest] = value

        self._fromOpenIDArgs(openid_args)

        return self

    @classmethod
    def fromOpenIDArgs(cls, openid_args):
        """Construct a Message from a parsed KVForm message.

        @raises InvalidOpenIDNamespace: if openid.ns is not in
            L{Message.allowed_openid_namespaces}
        """
        self = cls()
        self._fromOpenIDArgs(openid_args)
        return self

    def _fromOpenIDArgs(self, openid_args):
        ns_args = []

        # Resolve namespaces
        for rest, value in openid_args.items():
            try:
                ns_alias, ns_key = rest.split('.', 1)
            except ValueError:
                ns_alias = NULL_NAMESPACE
                ns_key = rest

            if ns_alias == 'ns':
                self.namespaces.addAlias(value, ns_key)
            elif ns_alias == NULL_NAMESPACE and ns_key == 'ns':
                # null namespace
                self.setOpenIDNamespace(value, False)
            else:
                ns_args.append((ns_alias, ns_key, value))

        # Implicitly set an OpenID namespace definition (OpenID 1)
        if not self.getOpenIDNamespace():
            self.setOpenIDNamespace(OPENID1_NS, True)

        # Actually put the pairs into the appropriate namespaces
        for (ns_alias, ns_key, value) in ns_args:
            ns_uri = self.namespaces.getNamespaceURI(ns_alias)
            if ns_uri is None:
                # we found a namespaced arg without a namespace URI defined
                ns_uri = self._getDefaultNamespace(ns_alias)
                if ns_uri is None:
                    ns_uri = self.getOpenIDNamespace()
                    ns_key = '%s.%s' % (ns_alias, ns_key)
                else:
                    self.namespaces.addAlias(ns_uri, ns_alias, implicit=True)

            self.setArg(ns_uri, ns_key, value)

    def _getDefaultNamespace(self, mystery_alias):
        """OpenID 1 compatibility: look for a default namespace URI to
        use for this alias."""
        global registered_aliases
        # Only try to map an alias to a default if it's an
        # OpenID 1.x message.
        if self.isOpenID1():
            return registered_aliases.get(mystery_alias)
        else:
            return None

    def setOpenIDNamespace(self, openid_ns_uri, implicit):
        """Set the OpenID namespace URI used in this message.

        @raises InvalidOpenIDNamespace: if the namespace is not in
            L{Message.allowed_openid_namespaces}
        """
        if isinstance(openid_ns_uri, bytes):
            openid_ns_uri = str(openid_ns_uri, encoding="utf-8")
        if openid_ns_uri not in self.allowed_openid_namespaces:
            raise InvalidOpenIDNamespace(openid_ns_uri)

        self.namespaces.addAlias(openid_ns_uri, NULL_NAMESPACE, implicit)
        self._openid_ns_uri = openid_ns_uri

    def getOpenIDNamespace(self):
        return self._openid_ns_uri

    def isOpenID1(self):
        return self.getOpenIDNamespace() in OPENID1_NAMESPACES

    def isOpenID2(self):
        return self.getOpenIDNamespace() == OPENID2_NS

    def fromKVForm(cls, kvform_string):
        """Create a Message from a KVForm string"""
        return cls.fromOpenIDArgs(kvform.kvToDict(kvform_string))

    fromKVForm = classmethod(fromKVForm)

    def copy(self):
        return copy.deepcopy(self)

    def toPostArgs(self):
        """
        Return all arguments with openid. in front of namespaced arguments.
        @return bytes
        """
        args = {}

        # Add namespace definitions to the output
        for ns_uri, alias in self.namespaces.items():
            if self.namespaces.isImplicit(ns_uri):
                continue
            if alias == NULL_NAMESPACE:
                ns_key = 'openid.ns'
            else:
                ns_key = 'openid.ns.' + alias
            args[ns_key] = oidutil.toUnicode(ns_uri)

        for (ns_uri, ns_key), value in self.args.items():
            key = self.getKey(ns_uri, ns_key)
            # Ensure the resulting value is an UTF-8 encoded *bytestring*.
            args[key] = oidutil.toUnicode(value)

        return args

    def toArgs(self):
        """Return all namespaced arguments, failing if any
        non-namespaced arguments exist."""
        # FIXME - undocumented exception
        post_args = self.toPostArgs()
        kvargs = {}
        for k, v in post_args.items():
            if not k.startswith('openid.'):
                raise ValueError(
                    'This message can only be encoded as a POST, because it '
                    'contains arguments that are not prefixed with "openid."')
            else:
                kvargs[k[7:]] = v

        return kvargs

    def toFormMarkup(self,
                     action_url,
                     form_tag_attrs=None,
                     submit_text="Continue"):
        """Generate HTML form markup that contains the values in this
        message, to be HTTP POSTed as x-www-form-urlencoded UTF-8.

        @param action_url: The URL to which the form will be POSTed
        @type action_url: str

        @param form_tag_attrs: Dictionary of attributes to be added to
            the form tag. 'accept-charset' and 'enctype' have defaults
            that can be overridden. If a value is supplied for
            'action' or 'method', it will be replaced.
        @type form_tag_attrs: {unicode: unicode}

        @param submit_text: The text that will appear on the submit
            button for this form.
        @type submit_text: unicode

        @returns: A string containing (X)HTML markup for a form that
            encodes the values in this Message object.
        @rtype: str
        """
        if ElementTree is None:
            raise RuntimeError('This function requires ElementTree.')

        assert action_url is not None

        form = ElementTree.Element('form')

        if form_tag_attrs:
            for name, attr in form_tag_attrs.items():
                form.attrib[name] = attr

        form.attrib['action'] = oidutil.toUnicode(action_url)
        form.attrib['method'] = 'post'
        form.attrib['accept-charset'] = 'UTF-8'
        form.attrib['enctype'] = 'application/x-www-form-urlencoded'

        for name, value in self.toPostArgs().items():
            attrs = {
                'type': 'hidden',
                'name': oidutil.toUnicode(name),
                'value': oidutil.toUnicode(value)
            }
            form.append(ElementTree.Element('input', attrs))

        submit = ElementTree.Element(
            'input',
            {'type': 'submit',
             'value': oidutil.toUnicode(submit_text)})
        form.append(submit)

        return str(ElementTree.tostring(form, encoding='utf-8'),
                   encoding="utf-8")

    def toURL(self, base_url):
        """Generate a GET URL with the parameters in this message
        attached as query parameters."""
        return oidutil.appendArgs(base_url, self.toPostArgs())

    def toKVForm(self):
        """Generate a KVForm string that contains the parameters in
        this message. This will fail if the message contains arguments
        outside of the 'openid.' prefix.
        """
        return kvform.dictToKV(self.toArgs())

    def toURLEncoded(self):
        """Generate an x-www-urlencoded string"""
        args = sorted(self.toPostArgs().items())
        return urllib.parse.urlencode(args)

    def _fixNS(self, namespace):
        """Convert an input value into the internally used values of
        this object

        @param namespace: The string or constant to convert
        @type namespace: str or unicode or BARE_NS or OPENID_NS
        """
        if isinstance(namespace, bytes):
            namespace = str(namespace, encoding="utf-8")

        if namespace == OPENID_NS:
            if self._openid_ns_uri is None:
                raise UndefinedOpenIDNamespace('OpenID namespace not set')
            else:
                namespace = self._openid_ns_uri

        if namespace != BARE_NS and not isinstance(namespace, str):
            raise TypeError(
                "Namespace must be BARE_NS, OPENID_NS or a string. got %r" %
                (namespace, ))

        if namespace != BARE_NS and ':' not in namespace:
            fmt = 'OpenID 2.0 namespace identifiers SHOULD be URIs. Got %r'
            warnings.warn(fmt % (namespace, ), DeprecationWarning)

            if namespace == 'sreg':
                fmt = 'Using %r instead of "sreg" as namespace'
                warnings.warn(
                    fmt % (SREG_URI, ),
                    DeprecationWarning, )
                return SREG_URI

        return namespace

    def hasKey(self, namespace, ns_key):
        namespace = self._fixNS(namespace)
        return (namespace, ns_key) in self.args

    def getKey(self, namespace, ns_key):
        """Get the key for a particular namespaced argument"""
        namespace = self._fixNS(namespace)
        if namespace == BARE_NS:
            return ns_key

        ns_alias = self.namespaces.getAlias(namespace)

        # No alias is defined, so no key can exist
        if ns_alias is None:
            return None

        if ns_alias == NULL_NAMESPACE:
            tail = ns_key
        else:
            tail = '%s.%s' % (ns_alias, ns_key)

        return 'openid.' + tail

    def getArg(self, namespace, key, default=None):
        """Get a value for a namespaced key.

        @param namespace: The namespace in the message for this key
        @type namespace: str

        @param key: The key to get within this namespace
        @type key: str

        @param default: The value to use if this key is absent from
            this message. Using the special value
            openid.message.no_default will result in this method
            raising a KeyError instead of returning the default.

        @rtype: str or the type of default
        @raises KeyError: if default is no_default
        @raises UndefinedOpenIDNamespace: if the message has not yet
            had an OpenID namespace set
        """
        namespace = self._fixNS(namespace)
        args_key = (namespace, key)
        try:
            return self.args[args_key]
        except KeyError:
            if default is no_default:
                raise KeyError((namespace, key))
            else:
                return default

    def getArgs(self, namespace):
        """Get the arguments that are defined for this namespace URI

        @returns: mapping from namespaced keys to values
        @returntype: dict of {str:bytes}
        """
        namespace = self._fixNS(namespace)
        args = []
        for ((pair_ns, ns_key), value) in self.args.items():
            if pair_ns == namespace:
                if isinstance(ns_key, bytes):
                    k = str(ns_key, encoding="utf-8")
                else:
                    k = ns_key
                if isinstance(value, bytes):
                    v = str(value, encoding="utf-8")
                else:
                    v = value
                args.append((k, v))
        return dict(args)

    def updateArgs(self, namespace, updates):
        """Set multiple key/value pairs in one call

        @param updates: The values to set
        @type updates: {unicode:unicode}
        """
        namespace = self._fixNS(namespace)
        for k, v in updates.items():
            self.setArg(namespace, k, v)

    def setArg(self, namespace, key, value):
        """Set a single argument in this namespace"""
        assert key is not None
        assert value is not None
        namespace = self._fixNS(namespace)
        # try to ensure that internally it's consistent, at least: str -> str
        if isinstance(value, bytes):
            value = str(value, encoding="utf-8")
        self.args[(namespace, key)] = value
        if not (namespace is BARE_NS):
            self.namespaces.add(namespace)

    def delArg(self, namespace, key):
        namespace = self._fixNS(namespace)
        del self.args[(namespace, key)]

    def __repr__(self):
        return "<%s.%s %r>" % (self.__class__.__module__,
                               self.__class__.__name__, self.args)

    def __eq__(self, other):
        return self.args == other.args

    def __ne__(self, other):
        return not (self == other)

    def getAliasedArg(self, aliased_key, default=None):
        if aliased_key == 'ns':
            return self.getOpenIDNamespace()

        if aliased_key.startswith('ns.'):
            uri = self.namespaces.getNamespaceURI(aliased_key[3:])
            if uri is None:
                if default == no_default:
                    raise KeyError
                else:
                    return default
            else:
                return uri

        try:
            alias, key = aliased_key.split('.', 1)
        except ValueError:
            # need more than x values to unpack
            ns = None
        else:
            ns = self.namespaces.getNamespaceURI(alias)

        if ns is None:
            key = aliased_key
            ns = self.getOpenIDNamespace()

        return self.getArg(ns, key, default)


class NamespaceMap(object):
    """Maintains a bijective map between namespace uris and aliases.
    """

    def __init__(self):
        self.alias_to_namespace = {}
        self.namespace_to_alias = {}
        self.implicit_namespaces = []

    def getAlias(self, namespace_uri):
        return self.namespace_to_alias.get(namespace_uri)

    def getNamespaceURI(self, alias):
        return self.alias_to_namespace.get(alias)

    def iterNamespaceURIs(self):
        """Return an iterator over the namespace URIs"""
        return iter(self.namespace_to_alias)

    def iterAliases(self):
        """Return an iterator over the aliases"""
        return iter(self.alias_to_namespace)

    def items(self):
        """Iterate over the mapping

        @returns: iterator of (namespace_uri, alias)
        """
        return self.namespace_to_alias.items()

    def addAlias(self, namespace_uri, desired_alias, implicit=False):
        """Add an alias from this namespace URI to the desired alias
        """
        if isinstance(namespace_uri, bytes):
            namespace_uri = str(namespace_uri, encoding="utf-8")
        # Check that desired_alias is not an openid protocol field as
        # per the spec.
        assert desired_alias not in OPENID_PROTOCOL_FIELDS, \
               "%r is not an allowed namespace alias" % (desired_alias,)

        # Check that desired_alias does not contain a period as per
        # the spec.
        if isinstance(desired_alias, str):
            assert '.' not in desired_alias, \
                   "%r must not contain a dot" % (desired_alias,)

        # Check that there is not a namespace already defined for
        # the desired alias
        current_namespace_uri = self.alias_to_namespace.get(desired_alias)
        if (current_namespace_uri is not None and
                current_namespace_uri != namespace_uri):

            fmt = ('Cannot map %r to alias %r. '
                   '%r is already mapped to alias %r')

            msg = fmt % (namespace_uri, desired_alias, current_namespace_uri,
                         desired_alias)
            raise KeyError(msg)

        # Check that there is not already a (different) alias for
        # this namespace URI
        alias = self.namespace_to_alias.get(namespace_uri)
        if alias is not None and alias != desired_alias:
            fmt = ('Cannot map %r to alias %r. '
                   'It is already mapped to alias %r')
            raise KeyError(fmt % (namespace_uri, desired_alias, alias))

        assert (desired_alias == NULL_NAMESPACE or
                type(desired_alias) in [str, str]), repr(desired_alias)
        assert namespace_uri not in self.implicit_namespaces
        self.alias_to_namespace[desired_alias] = namespace_uri
        self.namespace_to_alias[namespace_uri] = desired_alias
        if implicit:
            self.implicit_namespaces.append(namespace_uri)
        return desired_alias

    def add(self, namespace_uri):
        """Add this namespace URI to the mapping, without caring what
        alias it ends up with"""
        # See if this namespace is already mapped to an alias
        alias = self.namespace_to_alias.get(namespace_uri)
        if alias is not None:
            return alias

        # Fall back to generating a numerical alias
        i = 0
        while True:
            alias = 'ext' + str(i)
            try:
                self.addAlias(namespace_uri, alias)
            except KeyError:
                i += 1
            else:
                return alias

        assert False, "Not reached"

    def isDefined(self, namespace_uri):
        return namespace_uri in self.namespace_to_alias

    def __contains__(self, namespace_uri):
        return self.isDefined(namespace_uri)

    def isImplicit(self, namespace_uri):
        return namespace_uri in self.implicit_namespaces
