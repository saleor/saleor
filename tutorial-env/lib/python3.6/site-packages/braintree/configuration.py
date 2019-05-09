import braintree
from braintree.credentials_parser import CredentialsParser
from braintree.environment import Environment
from braintree.exceptions.configuration_error import ConfigurationError
from braintree.util.graphql_client import GraphQLClient


class Configuration(object):
    """
    A class representing the configuration of your Braintree account.
    You must call configure before any other Braintree operations. ::

        braintree.Configuration.configure(
            braintree.Environment.Sandbox,
            "your_merchant_id",
            "your_public_key",
            "your_private_key"
        )
    """

    @staticmethod
    def configure(environment, merchant_id, public_key, private_key, **kwargs):
        Configuration.environment = Environment.parse_environment(environment)
        Configuration.merchant_id = merchant_id
        Configuration.public_key = public_key
        Configuration.private_key = private_key
        Configuration.default_http_strategy = kwargs.get("http_strategy", None)
        Configuration.timeout = kwargs.get("timeout", 60)
        Configuration.wrap_http_exceptions = kwargs.get("wrap_http_exceptions", False)

    @staticmethod
    def for_partner(environment, partner_id, public_key, private_key, **kwargs):
        return Configuration(
            environment=environment,
            merchant_id=partner_id,
            public_key=public_key,
            private_key=private_key,
            http_strategy=kwargs.get("http_strategy", None),
            timeout=kwargs.get("timeout", 60),
            wrap_http_exceptions=kwargs.get("wrap_http_exceptions", False)
        )

    @staticmethod
    def gateway():
        return braintree.braintree_gateway.BraintreeGateway(config=Configuration.instantiate())

    @staticmethod
    def instantiate():
        return Configuration(
            environment=Configuration.environment,
            merchant_id=Configuration.merchant_id,
            public_key=Configuration.public_key,
            private_key=Configuration.private_key,
            http_strategy=Configuration.default_http_strategy,
            timeout=Configuration.timeout,
            wrap_http_exceptions=Configuration.wrap_http_exceptions
        )

    @staticmethod
    def api_version():
        return "5"

    @staticmethod
    def graphql_api_version():
        return "2018-09-10"

    def __init__(self, environment=None, merchant_id=None, public_key=None, private_key=None,
                 client_id=None, client_secret=None, access_token=None, *args, **kwargs):
        if len(args) == 2:
            public_key, private_key = args

        parser = CredentialsParser(client_id=client_id, client_secret=client_secret,
                                   access_token=access_token)
        if parser.access_token is not None:
            parser.parse_access_token()
            self.environment = parser.environment
            self.merchant_id = parser.merchant_id
        elif parser.client_id is not None or parser.client_secret is not None:
            parser.parse_client_credentials()
            self.environment = parser.environment
            self.merchant_id = merchant_id
        else:
            self.environment = Environment.parse_environment(environment)
            if merchant_id == "":
                raise ConfigurationError("Missing merchant_id")
            else:
                self.merchant_id = merchant_id

            if public_key == "":
                raise ConfigurationError("Missing public_key")
            else:
                self.public_key = public_key

            if private_key == "":
                raise ConfigurationError("Missing private_key")
            else:
                self.private_key = private_key

        self.client_id = parser.client_id
        self.client_secret = parser.client_secret
        self.access_token = parser.access_token
        self.timeout = kwargs.get("timeout", 60)
        self.wrap_http_exceptions = kwargs.get("wrap_http_exceptions", False)

        http_strategy = kwargs.get("http_strategy", None)

        if http_strategy:
            self._http_strategy = http_strategy(self, self.environment)
        else:
            self._http_strategy = self.http()

    def base_merchant_path(self):
        return "/merchants/" + self.merchant_id

    def base_url(self):
        return self.environment.protocol + self.environment.server_and_port

    def graphql_base_url(self):
        return self.environment.protocol + self.environment.graphql_server_and_port + "/graphql"

    def http(self):
        return braintree.util.http.Http(self)

    def graphql_client(self):
        return GraphQLClient(self)

    def http_strategy(self):
        return self._http_strategy

    def has_client_credentials(self):
        return self.client_secret is not None and self.client_id is not None

    def assert_has_client_credentials(self):
        if not self.has_client_credentials():
            raise ConfigurationError("client_id and client_secret are required")

    def has_access_token(self):
        return self.access_token is not None
