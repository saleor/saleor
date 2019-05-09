"""An implementation of the OpenID Provider Authentication Policy
Extension 1.0, Draft 5

@see: http://openid.net/developers/specs/

@since: 2.1.0
"""

__all__ = [
    'Request',
    'Response',
    'ns_uri',
    'AUTH_PHISHING_RESISTANT',
    'AUTH_MULTI_FACTOR',
    'AUTH_MULTI_FACTOR_PHYSICAL',
    'LEVELS_NIST',
    'LEVELS_JISA',
]

from openid.extension import Extension
import warnings
import re

ns_uri = "http://specs.openid.net/extensions/pape/1.0"

AUTH_MULTI_FACTOR_PHYSICAL = \
    'http://schemas.openid.net/pape/policies/2007/06/multi-factor-physical'
AUTH_MULTI_FACTOR = \
    'http://schemas.openid.net/pape/policies/2007/06/multi-factor'
AUTH_PHISHING_RESISTANT = \
    'http://schemas.openid.net/pape/policies/2007/06/phishing-resistant'
AUTH_NONE = \
    'http://schemas.openid.net/pape/policies/2007/06/none'

TIME_VALIDATOR = re.compile('^\d\d\d\d-\d\d-\d\dT\d\d:\d\d:\d\dZ$')

LEVELS_NIST = 'http://csrc.nist.gov/publications/nistpubs/800-63/SP800-63V1_0_2.pdf'
LEVELS_JISA = 'http://www.jisa.or.jp/spec/auth_level.html'


class PAPEExtension(Extension):
    _default_auth_level_aliases = {
        'nist': LEVELS_NIST,
        'jisa': LEVELS_JISA,
    }

    def __init__(self):
        self.auth_level_aliases = self._default_auth_level_aliases.copy()

    def _addAuthLevelAlias(self, auth_level_uri, alias=None):
        """Add an auth level URI alias to this request.

        @param auth_level_uri: The auth level URI to send in the
            request.

        @param alias: The namespace alias to use for this auth level
            in this message. May be None if the alias is not
            important.
        """
        if alias is None:
            try:
                alias = self._getAlias(auth_level_uri)
            except KeyError:
                alias = self._generateAlias()
        else:
            existing_uri = self.auth_level_aliases.get(alias)
            if existing_uri is not None and existing_uri != auth_level_uri:
                raise KeyError('Attempting to redefine alias %r from %r to %r',
                               alias, existing_uri, auth_level_uri)

        self.auth_level_aliases[alias] = auth_level_uri

    def _generateAlias(self):
        """Return an unused auth level alias"""
        for i in range(1000):
            alias = 'cust%d' % (i, )
            if alias not in self.auth_level_aliases:
                return alias

        raise RuntimeError('Could not find an unused alias (tried 1000!)')

    def _getAlias(self, auth_level_uri):
        """Return the alias for the specified auth level URI.

        @raises KeyError: if no alias is defined
        """
        for (alias, existing_uri) in self.auth_level_aliases.items():
            if auth_level_uri == existing_uri:
                return alias

        raise KeyError(auth_level_uri)


class Request(PAPEExtension):
    """A Provider Authentication Policy request, sent from a relying
    party to a provider

    @ivar preferred_auth_policies: The authentication policies that
        the relying party prefers
    @type preferred_auth_policies: [str]

    @ivar max_auth_age: The maximum time, in seconds, that the relying
        party wants to allow to have elapsed before the user must
        re-authenticate
    @type max_auth_age: int or NoneType

    @ivar preferred_auth_level_types: Ordered list of authentication
        level namespace URIs

    @type preferred_auth_level_types: [str]
    """

    ns_alias = 'pape'

    def __init__(self,
                 preferred_auth_policies=None,
                 max_auth_age=None,
                 preferred_auth_level_types=None):
        super(Request, self).__init__()
        if preferred_auth_policies is None:
            preferred_auth_policies = []

        self.preferred_auth_policies = preferred_auth_policies
        self.max_auth_age = max_auth_age
        self.preferred_auth_level_types = []

        if preferred_auth_level_types is not None:
            for auth_level in preferred_auth_level_types:
                self.addAuthLevel(auth_level)

    def __bool__(self):
        return bool(self.preferred_auth_policies or
                    self.max_auth_age is not None or
                    self.preferred_auth_level_types)

    def addPolicyURI(self, policy_uri):
        """Add an acceptable authentication policy URI to this request

        This method is intended to be used by the relying party to add
        acceptable authentication types to the request.

        @param policy_uri: The identifier for the preferred type of
            authentication.
        @see: http://openid.net/specs/openid-provider-authentication-policy-extension-1_0-05.html#auth_policies
        """
        if policy_uri not in self.preferred_auth_policies:
            self.preferred_auth_policies.append(policy_uri)

    def addAuthLevel(self, auth_level_uri, alias=None):
        self._addAuthLevelAlias(auth_level_uri, alias)
        if auth_level_uri not in self.preferred_auth_level_types:
            self.preferred_auth_level_types.append(auth_level_uri)

    def getExtensionArgs(self):
        """@see: C{L{Extension.getExtensionArgs}}
        """
        ns_args = {
            'preferred_auth_policies': ' '.join(self.preferred_auth_policies),
        }

        if self.max_auth_age is not None:
            ns_args['max_auth_age'] = str(self.max_auth_age)

        if self.preferred_auth_level_types:
            preferred_types = []

            for auth_level_uri in self.preferred_auth_level_types:
                alias = self._getAlias(auth_level_uri)
                ns_args['auth_level.ns.%s' % (alias, )] = auth_level_uri
                preferred_types.append(alias)

            ns_args['preferred_auth_level_types'] = ' '.join(preferred_types)

        return ns_args

    def fromOpenIDRequest(cls, request):
        """Instantiate a Request object from the arguments in a
        C{checkid_*} OpenID message
        """
        self = cls()
        args = request.message.getArgs(self.ns_uri)
        is_openid1 = request.message.isOpenID1()

        if args == {}:
            return None

        self.parseExtensionArgs(args, is_openid1)
        return self

    fromOpenIDRequest = classmethod(fromOpenIDRequest)

    def parseExtensionArgs(self, args, is_openid1, strict=False):
        """Set the state of this request to be that expressed in these
        PAPE arguments

        @param args: The PAPE arguments without a namespace

        @param strict: Whether to raise an exception if the input is
            out of spec or otherwise malformed. If strict is false,
            malformed input will be ignored.

        @param is_openid1: Whether the input should be treated as part
            of an OpenID1 request

        @rtype: None

        @raises ValueError: When the max_auth_age is not parseable as
            an integer
        """

        # preferred_auth_policies is a space-separated list of policy URIs
        self.preferred_auth_policies = []

        policies_str = args.get('preferred_auth_policies')
        if policies_str:
            if isinstance(policies_str, bytes):
                policies_str = str(policies_str, encoding="utf-8")
            for uri in policies_str.split(' '):
                if uri not in self.preferred_auth_policies:
                    self.preferred_auth_policies.append(uri)

        # max_auth_age is base-10 integer number of seconds
        max_auth_age_str = args.get('max_auth_age')
        self.max_auth_age = None

        if max_auth_age_str:
            try:
                self.max_auth_age = int(max_auth_age_str)
            except ValueError:
                if strict:
                    raise

        # Parse auth level information
        preferred_auth_level_types = args.get('preferred_auth_level_types')
        if preferred_auth_level_types:
            aliases = preferred_auth_level_types.strip().split()

            for alias in aliases:
                key = 'auth_level.ns.%s' % (alias, )
                try:
                    uri = args[key]
                except KeyError:
                    if is_openid1:
                        uri = self._default_auth_level_aliases.get(alias)
                    else:
                        uri = None

                if uri is None:
                    if strict:
                        raise ValueError('preferred auth level %r is not '
                                         'defined in this message' % (alias, ))
                else:
                    self.addAuthLevel(uri, alias)

    def preferredTypes(self, supported_types):
        """Given a list of authentication policy URIs that a provider
        supports, this method returns the subsequence of those types
        that are preferred by the relying party.

        @param supported_types: A sequence of authentication policy
            type URIs that are supported by a provider

        @returns: The sub-sequence of the supported types that are
            preferred by the relying party. This list will be ordered
            in the order that the types appear in the supported_types
            sequence, and may be empty if the provider does not prefer
            any of the supported authentication types.

        @returntype: [str]
        """
        return list(
            filter(self.preferred_auth_policies.__contains__, supported_types))


Request.ns_uri = ns_uri


class Response(PAPEExtension):
    """A Provider Authentication Policy response, sent from a provider
    to a relying party

    @ivar auth_policies: List of authentication policies conformed to
        by this OpenID assertion, represented as policy URIs
    """

    ns_alias = 'pape'

    def __init__(self, auth_policies=None, auth_time=None, auth_levels=None):
        super(Response, self).__init__()
        if auth_policies:
            self.auth_policies = auth_policies
        else:
            self.auth_policies = []

        self.auth_time = auth_time
        self.auth_levels = {}

        if auth_levels is None:
            auth_levels = {}

        for uri, level in auth_levels.items():
            self.setAuthLevel(uri, level)

    def setAuthLevel(self, level_uri, level, alias=None):
        """Set the value for the given auth level type.

        @param level: string representation of an authentication level
            valid for level_uri

        @param alias: An optional namespace alias for the given auth
            level URI. May be omitted if the alias is not
            significant. The library will use a reasonable default for
            widely-used auth level types.
        """
        self._addAuthLevelAlias(level_uri, alias)
        self.auth_levels[level_uri] = level

    def getAuthLevel(self, level_uri):
        """Return the auth level for the specified auth level
        identifier

        @returns: A string that should map to the auth levels defined
            for the auth level type

        @raises KeyError: If the auth level type is not present in
            this message
        """
        return self.auth_levels[level_uri]

    def _getNISTAuthLevel(self):
        try:
            return int(self.getAuthLevel(LEVELS_NIST))
        except KeyError:
            return None

    nist_auth_level = property(
        _getNISTAuthLevel,
        doc="Backward-compatibility accessor for the NIST auth level")

    def addPolicyURI(self, policy_uri):
        """Add a authentication policy to this response

        This method is intended to be used by the provider to add a
        policy that the provider conformed to when authenticating the user.

        @param policy_uri: The identifier for the preferred type of
            authentication.
        @see: http://openid.net/specs/openid-provider-authentication-policy-extension-1_0-01.html#auth_policies
        """
        if policy_uri == AUTH_NONE:
            raise RuntimeError(
                'To send no policies, do not set any on the response.')

        if policy_uri not in self.auth_policies:
            self.auth_policies.append(policy_uri)

    def fromSuccessResponse(cls, success_response):
        """Create a C{L{Response}} object from a successful OpenID
        library response
        (C{L{openid.consumer.consumer.SuccessResponse}}) response
        message

        @param success_response: A SuccessResponse from consumer.complete()
        @type success_response: C{L{openid.consumer.consumer.SuccessResponse}}

        @rtype: Response or None
        @returns: A provider authentication policy response from the
            data that was supplied with the C{id_res} response or None
            if the provider sent no signed PAPE response arguments.
        """
        self = cls()

        # PAPE requires that the args be signed.
        args = success_response.getSignedNS(self.ns_uri)
        is_openid1 = success_response.isOpenID1()

        # Only try to construct a PAPE response if the arguments were
        # signed in the OpenID response.  If not, return None.
        if args is not None:
            self.parseExtensionArgs(args, is_openid1)
            return self
        else:
            return None

    def parseExtensionArgs(self, args, is_openid1, strict=False):
        """Parse the provider authentication policy arguments into the
        internal state of this object

        @param args: unqualified provider authentication policy
            arguments

        @param strict: Whether to raise an exception when bad data is
            encountered

        @returns: None. The data is parsed into the internal fields of
            this object.
        """
        policies_str = args.get('auth_policies')
        if policies_str:
            auth_policies = policies_str.split(' ')
        elif strict:
            raise ValueError('Missing auth_policies')
        else:
            auth_policies = []

        if (len(auth_policies) > 1 and strict and AUTH_NONE in auth_policies):
            raise ValueError('Got some auth policies, as well as the special '
                             '"none" URI: %r' % (auth_policies, ))

        if 'none' in auth_policies:
            msg = '"none" used as a policy URI (see PAPE draft < 5)'
            if strict:
                raise ValueError(msg)
            else:
                warnings.warn(msg, stacklevel=2)

        auth_policies = [
            u for u in auth_policies if u not in ['none', AUTH_NONE]
        ]

        self.auth_policies = auth_policies

        for (key, val) in args.items():
            if key.startswith('auth_level.'):
                alias = key[11:]

                # skip the already-processed namespace declarations
                if alias.startswith('ns.'):
                    continue

                try:
                    uri = args['auth_level.ns.%s' % (alias, )]
                except KeyError:
                    if is_openid1:
                        uri = self._default_auth_level_aliases.get(alias)
                    else:
                        uri = None

                if uri is None:
                    if strict:
                        raise ValueError('Undefined auth level alias: %r' %
                                         (alias, ))
                else:
                    self.setAuthLevel(uri, val, alias)

        auth_time = args.get('auth_time')
        if auth_time:
            if TIME_VALIDATOR.match(auth_time):
                self.auth_time = auth_time
            elif strict:
                raise ValueError("auth_time must be in RFC3339 format")

    fromSuccessResponse = classmethod(fromSuccessResponse)

    def getExtensionArgs(self):
        """@see: C{L{Extension.getExtensionArgs}}
        """
        if len(self.auth_policies) == 0:
            ns_args = {
                'auth_policies': AUTH_NONE,
            }
        else:
            ns_args = {
                'auth_policies': ' '.join(self.auth_policies),
            }

        for level_type, level in self.auth_levels.items():
            alias = self._getAlias(level_type)
            ns_args['auth_level.ns.%s' % (alias, )] = level_type
            ns_args['auth_level.%s' % (alias, )] = str(level)

        if self.auth_time is not None:
            if not TIME_VALIDATOR.match(self.auth_time):
                raise ValueError('auth_time must be in RFC3339 format')

            ns_args['auth_time'] = self.auth_time

        return ns_args


Response.ns_uri = ns_uri
