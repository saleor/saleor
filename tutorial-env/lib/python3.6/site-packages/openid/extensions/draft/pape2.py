"""An implementation of the OpenID Provider Authentication Policy
Extension 1.0

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
]

from openid.extension import Extension
import re

ns_uri = "http://specs.openid.net/extensions/pape/1.0"

AUTH_MULTI_FACTOR_PHYSICAL = \
    'http://schemas.openid.net/pape/policies/2007/06/multi-factor-physical'
AUTH_MULTI_FACTOR = \
    'http://schemas.openid.net/pape/policies/2007/06/multi-factor'
AUTH_PHISHING_RESISTANT = \
    'http://schemas.openid.net/pape/policies/2007/06/phishing-resistant'

TIME_VALIDATOR = re.compile('^\d\d\d\d-\d\d-\d\dT\d\d:\d\d:\d\dZ$')


class Request(Extension):
    """A Provider Authentication Policy request, sent from a relying
    party to a provider

    @ivar preferred_auth_policies: The authentication policies that
        the relying party prefers
    @type preferred_auth_policies: [str]

    @ivar max_auth_age: The maximum time, in seconds, that the relying
        party wants to allow to have elapsed before the user must
        re-authenticate
    @type max_auth_age: int or NoneType
    """

    ns_alias = 'pape'

    def __init__(self, preferred_auth_policies=None, max_auth_age=None):
        super(Request, self).__init__()
        if not preferred_auth_policies:
            preferred_auth_policies = []

        self.preferred_auth_policies = preferred_auth_policies
        self.max_auth_age = max_auth_age

    def __bool__(self):
        return bool(self.preferred_auth_policies or
                    self.max_auth_age is not None)

    def addPolicyURI(self, policy_uri):
        """Add an acceptable authentication policy URI to this request

        This method is intended to be used by the relying party to add
        acceptable authentication types to the request.

        @param policy_uri: The identifier for the preferred type of
            authentication.
        @see: http://openid.net/specs/openid-provider-authentication-policy-extension-1_0-01.html#auth_policies
        """
        if policy_uri not in self.preferred_auth_policies:
            self.preferred_auth_policies.append(policy_uri)

    def getExtensionArgs(self):
        """@see: C{L{Extension.getExtensionArgs}}
        """
        ns_args = {
            'preferred_auth_policies': ' '.join(self.preferred_auth_policies)
        }

        if self.max_auth_age is not None:
            ns_args['max_auth_age'] = str(self.max_auth_age)

        return ns_args

    def fromOpenIDRequest(cls, request):
        """Instantiate a Request object from the arguments in a
        C{checkid_*} OpenID message
        """
        self = cls()
        args = request.message.getArgs(self.ns_uri)

        if args == {}:
            return None

        self.parseExtensionArgs(args)
        return self

    fromOpenIDRequest = classmethod(fromOpenIDRequest)

    def parseExtensionArgs(self, args):
        """Set the state of this request to be that expressed in these
        PAPE arguments

        @param args: The PAPE arguments without a namespace

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
                pass

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


class Response(Extension):
    """A Provider Authentication Policy response, sent from a provider
    to a relying party
    """

    ns_alias = 'pape'

    def __init__(self,
                 auth_policies=None,
                 auth_time=None,
                 nist_auth_level=None):
        super(Response, self).__init__()
        if auth_policies:
            self.auth_policies = auth_policies
        else:
            self.auth_policies = []

        self.auth_time = auth_time
        self.nist_auth_level = nist_auth_level

    def addPolicyURI(self, policy_uri):
        """Add a authentication policy to this response

        This method is intended to be used by the provider to add a
        policy that the provider conformed to when authenticating the user.

        @param policy_uri: The identifier for the preferred type of
            authentication.
        @see: http://openid.net/specs/openid-provider-authentication-policy-extension-1_0-01.html#auth_policies
        """
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

        # Only try to construct a PAPE response if the arguments were
        # signed in the OpenID response.  If not, return None.
        if args is not None:
            self.parseExtensionArgs(args)
            return self
        else:
            return None

    def parseExtensionArgs(self, args, strict=False):
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
        if policies_str and policies_str != 'none':
            self.auth_policies = policies_str.split(' ')

        nist_level_str = args.get('nist_auth_level')
        if nist_level_str:
            try:
                nist_level = int(nist_level_str)
            except ValueError:
                if strict:
                    raise ValueError(
                        'nist_auth_level must be an integer between '
                        'zero and four, inclusive')
                else:
                    self.nist_auth_level = None
            else:
                if 0 <= nist_level < 5:
                    self.nist_auth_level = nist_level

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
                'auth_policies': 'none',
            }
        else:
            ns_args = {
                'auth_policies': ' '.join(self.auth_policies),
            }

        if self.nist_auth_level is not None:
            if self.nist_auth_level not in list(range(0, 5)):
                raise ValueError('nist_auth_level must be an integer between '
                                 'zero and four, inclusive')
            ns_args['nist_auth_level'] = str(self.nist_auth_level)

        if self.auth_time is not None:
            if not TIME_VALIDATOR.match(self.auth_time):
                raise ValueError('auth_time must be in RFC3339 format')

            ns_args['auth_time'] = self.auth_time

        return ns_args


Response.ns_uri = ns_uri
