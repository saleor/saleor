"""
Backend for SAML 2.0 support

Terminology:

"Service Provider" (SP): Your web app
"Identity Provider" (IdP): The third-party site that is authenticating
                           users via SAML
"""
from onelogin.saml2.auth import OneLogin_Saml2_Auth
from onelogin.saml2.settings import OneLogin_Saml2_Settings

from .base import BaseAuth
from ..exceptions import AuthFailed, AuthMissingParameter

# Helpful constants:
OID_COMMON_NAME = "urn:oid:2.5.4.3"
OID_EDU_PERSON_PRINCIPAL_NAME = "urn:oid:1.3.6.1.4.1.5923.1.1.1.6"
OID_EDU_PERSON_ENTITLEMENT = "urn:oid:1.3.6.1.4.1.5923.1.1.1.7"
OID_GIVEN_NAME = "urn:oid:2.5.4.42"
OID_MAIL = "urn:oid:0.9.2342.19200300.100.1.3"
OID_SURNAME = "urn:oid:2.5.4.4"
OID_USERID = "urn:oid:0.9.2342.19200300.100.1.1"


class SAMLIdentityProvider(object):
    """Wrapper around configuration for a SAML Identity provider"""
    def __init__(self, name, **kwargs):
        """Load and parse configuration"""
        self.name = name
        # name should be a slug and must not contain a colon, which
        # could conflict with uid prefixing:
        assert ':' not in self.name and ' ' not in self.name, \
            'IdP "name" should be a slug (short, no spaces)'
        self.conf = kwargs

    def get_user_permanent_id(self, attributes):
        """
        The most important method: Get a permanent, unique identifier
        for this user from the attributes supplied by the IdP.

        If you want to use the NameID, it's available via
        attributes['name_id']
        """
        uid = attributes[self.conf.get('attr_user_permanent_id', OID_USERID)]
        if isinstance(uid, list):
            uid = uid[0]
        return uid

    # Attributes processing:
    def get_user_details(self, attributes):
        """
        Given the SAML attributes extracted from the SSO response, get
        the user data like name.
        """
        return {
            'fullname': self.get_attr(attributes, 'attr_full_name',
                                      OID_COMMON_NAME),
            'first_name': self.get_attr(attributes, 'attr_first_name',
                                        OID_GIVEN_NAME),
            'last_name': self.get_attr(attributes, 'attr_last_name',
                                       OID_SURNAME),
            'username': self.get_attr(attributes, 'attr_username',
                                      OID_USERID),
            'email': self.get_attr(attributes, 'attr_email',
                                   OID_MAIL),
        }

    def get_attr(self, attributes, conf_key, default_attribute):
        """
        Internal helper method.
        Get the attribute 'default_attribute' out of the attributes,
        unless self.conf[conf_key] overrides the default by specifying
        another attribute to use.
        """
        key = self.conf.get(conf_key, default_attribute)
        value = attributes[key] if key in attributes else None
        if isinstance(value, list):
            value = value[0]
        return value

    @property
    def entity_id(self):
        """Get the entity ID for this IdP"""
        # Required. e.g. "https://idp.testshib.org/idp/shibboleth"
        return self.conf['entity_id']

    @property
    def sso_url(self):
        """Get the SSO URL for this IdP"""
        # Required. e.g.
        # "https://idp.testshib.org/idp/profile/SAML2/Redirect/SSO"
        return self.conf['url']

    @property
    def saml_config_dict(self):
        """Get the IdP configuration dict in the format required by
        python-saml"""
        result = {
            'entityId': self.entity_id,
            'singleSignOnService': {
                'url': self.sso_url,
                # python-saml only supports Redirect
                'binding': 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect'
            },
        }
        cert = self.conf.get('x509cert', None)
        if cert:
            result['x509cert'] = cert
            return result
        cert = self.conf.get('x509certMulti', None)
        if cert:
            result['x509certMulti'] = cert
            return result
        raise KeyError("IDP must contain x509cert or x509certMulti")


class DummySAMLIdentityProvider(SAMLIdentityProvider):
    """
    A placeholder IdP used when we must specify something, e.g. when
    generating SP metadata.

    If OneLogin_Saml2_Auth is modified to not always require IdP
    config, this can be removed.
    """
    def __init__(self):
        super(DummySAMLIdentityProvider, self).__init__(
            'dummy',
            entity_id='https://dummy.none/saml2',
            url='https://dummy.none/SSO',
            x509cert=''
        )


class SAMLAuth(BaseAuth):
    """
    PSA Backend that implements SAML 2.0 Service Provider (SP) functionality.

    Unlike all of the other backends, this one can be configured to work with
    many identity providers (IdPs). For example, a University that belongs to a
    Shibboleth federation may support authentication via ~100 partner
    universities. Also, the IdP configuration can be changed at runtime if you
    require that functionality - just subclass this and override `get_idp()`.

    Several settings are required. Here's an example:

    SOCIAL_AUTH_SAML_SP_ENTITY_ID = "https://saml.example.com/"
    SOCIAL_AUTH_SAML_SP_PUBLIC_CERT = "... X.509 certificate string ..."
    SOCIAL_AUTH_SAML_SP_PRIVATE_KEY = "... private key ..."
    SOCIAL_AUTH_SAML_ORG_INFO = {
        "en-US": {
            "name": "example",
            "displayname": "Example Inc.",
            "url": "http://example.com"
        }
    }
    SOCIAL_AUTH_SAML_TECHNICAL_CONTACT = {
        "givenName": "Tech Gal",
        "emailAddress": "technical@example.com"
    }
    SOCIAL_AUTH_SAML_SUPPORT_CONTACT = {
        "givenName": "Support Guy",
        "emailAddress": "support@example.com"
    }
    SOCIAL_AUTH_SAML_ENABLED_IDPS = {
        "testshib": {
            "entity_id": "https://idp.testshib.org/idp/shibboleth",
            "url": "https://idp.testshib.org/idp/profile/SAML2/Redirect/SSO",
            "x509cert": "MIIEDjCCAvagAwIBAgIBADANBgkqhkiG9w0B...
                        ...8Bbnl+ev0peYzxFyF5sQA==",
        }
    }

    Optional settings:
    SOCIAL_AUTH_SAML_SP_EXTRA = {}
    SOCIAL_AUTH_SAML_SECURITY_CONFIG = {}
    """
    name = "saml"
    EXTRA_DATA = []

    def get_idp(self, idp_name):
        """Given the name of an IdP, get a SAMLIdentityProvider instance"""
        idp_config = self.setting('ENABLED_IDPS')[idp_name]
        return SAMLIdentityProvider(idp_name, **idp_config)

    def generate_saml_config(self, idp=None):
        """
        Generate the configuration required to instantiate OneLogin_Saml2_Auth
        """
        # The shared absolute URL that all IdPs redirect back to -
        # this is specified in our metadata.xml:
        abs_completion_url = self.redirect_uri
        config = {
            'contactPerson': {
                'technical': self.setting('TECHNICAL_CONTACT'),
                'support': self.setting('SUPPORT_CONTACT')
            },
            'debug': True,
            'idp': idp.saml_config_dict if idp else {},
            'organization': self.setting('ORG_INFO'),
            'security': {
                'metadataValidUntil': '',
                'metadataCacheDuration': 'P10D',  # metadata valid for ten days
            },
            'sp': {
                'assertionConsumerService': {
                    'url': abs_completion_url,
                    # python-saml only supports HTTP-POST
                    'binding': 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST'
                },
                'entityId': self.setting('SP_ENTITY_ID'),
                'x509cert': self.setting('SP_PUBLIC_CERT'),
                'privateKey': self.setting('SP_PRIVATE_KEY'),
            },
            'strict': True,  # We must force strict mode - for security
        }
        config["security"].update(self.setting("SECURITY_CONFIG", {}))
        config["sp"].update(self.setting("SP_EXTRA", {}))
        return config

    def generate_metadata_xml(self):
        """
        Helper method that can be used from your web app to generate the XML
        metadata required to link your web app as a Service Provider.

        Returns (metadata XML string, list of errors)

        Example usage (Django):
            from ..apps.django_app.utils import load_strategy, \
                                                     load_backend
            def saml_metadata_view(request):
                complete_url = reverse('social:complete', args=("saml", ))
                saml_backend = load_backend(load_strategy(request), "saml",
                                            complete_url)
                metadata, errors = saml_backend.generate_metadata_xml()
                if not errors:
                    return HttpResponse(content=metadata,
                                        content_type='text/xml')
                return HttpResponseServerError(content=', '.join(errors))
        """
        config = self.generate_saml_config()
        saml_settings = OneLogin_Saml2_Settings(
            config,
            sp_validation_only=True
        )
        metadata = saml_settings.get_sp_metadata()
        errors = saml_settings.validate_metadata(metadata)
        return metadata, errors

    def _create_saml_auth(self, idp):
        """Get an instance of OneLogin_Saml2_Auth"""
        config = self.generate_saml_config(idp)
        request_info = {
            'https': 'on' if self.strategy.request_is_secure() else 'off',
            'http_host': self.strategy.request_host(),
            'script_name': self.strategy.request_path(),
            'server_port': self.strategy.request_port(),
            'get_data': self.strategy.request_get(),
            'post_data': self.strategy.request_post(),
        }
        return OneLogin_Saml2_Auth(request_info, config)

    def auth_url(self):
        """Get the URL to which we must redirect in order to
        authenticate the user"""
        try:
            idp_name = self.strategy.request_data()['idp']
        except KeyError:
            raise AuthMissingParameter(self, 'idp')
        auth = self._create_saml_auth(idp=self.get_idp(idp_name))
        # Below, return_to sets the RelayState, which can contain
        # arbitrary data.  We use it to store the specific SAML IdP
        # name, since we multiple IdPs share the same auth_complete
        # URL.
        return auth.login(return_to=idp_name)

    def get_user_details(self, response):
        """Get user details like full name, email, etc. from the
        response - see auth_complete"""
        idp = self.get_idp(response['idp_name'])
        return idp.get_user_details(response['attributes'])

    def get_user_id(self, details, response):
        """
        Get the permanent ID for this user from the response.
        We prefix each ID with the name of the IdP so that we can
        connect multiple IdPs to this user.
        """
        idp = self.get_idp(response['idp_name'])
        uid = idp.get_user_permanent_id(response['attributes'])
        return '{0}:{1}'.format(idp.name, uid)

    def auth_complete(self, *args, **kwargs):
        """
        The user has been redirected back from the IdP and we should
        now log them in, if everything checks out.
        """
        idp_name = self.strategy.request_data()['RelayState']
        idp = self.get_idp(idp_name)
        auth = self._create_saml_auth(idp)
        auth.process_response()
        errors = auth.get_errors()
        if errors or not auth.is_authenticated():
            reason = auth.get_last_error_reason()
            raise AuthFailed(
                self, 'SAML login failed: {0} ({1})'.format(errors, reason)
            )

        attributes = auth.get_attributes()
        attributes['name_id'] = auth.get_nameid()
        self._check_entitlements(idp, attributes)
        response = {
            'idp_name': idp_name,
            'attributes': attributes,
            'session_index': auth.get_session_index(),
        }
        kwargs.update({'response': response, 'backend': self})
        return self.strategy.authenticate(*args, **kwargs)

    def extra_data(self, user, uid, response, details=None, *args, **kwargs):
        return super(SAMLAuth, self).extra_data(user, uid,
                                                response['attributes'],
                                                details=details,
                                                *args, **kwargs)

    def _check_entitlements(self, idp, attributes):
        """
        Additional verification of a SAML response before
        authenticating the user.

        Subclasses can override this method if they need custom
        validation code, such as requiring the presence of an
        eduPersonEntitlement.

        raise social_core.exceptions.AuthForbidden if the user should not
        be authenticated, or do nothing to allow the login pipeline to
        continue.
        """
        pass
