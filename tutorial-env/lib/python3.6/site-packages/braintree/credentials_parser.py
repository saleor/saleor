import os
import sys
import braintree
from braintree.exceptions.configuration_error import ConfigurationError
from braintree.environment import Environment

class CredentialsParser(object):
    def __init__(self, client_id=None, client_secret=None, access_token=None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = access_token

    def parse_client_credentials(self):
        if self.client_id is None and self.client_secret is not None:
            raise ConfigurationError("Missing client_id when constructing BraintreeGateway")
        if self.client_secret is None and self.client_id is not None:
            raise ConfigurationError("Missing client_secret when constructing BraintreeGateway")
        if not self.client_id.startswith("client_id"):
            raise ConfigurationError("Value passed for client_id is not a client_id")
        if not self.client_secret.startswith("client_secret"):
            raise ConfigurationError("Value passed for client_secret is not a client_secret")

        client_id_environment = self.get_environment(self.client_id)
        client_secret_environment = self.get_environment(self.client_secret)

        if client_id_environment is client_secret_environment:
            self.environment = client_id_environment
        else:
            raise ConfigurationError(" ".join([
                "Mismatched credential environments: client_id environment is:",
                str(client_id_environment),
                "and client_secret environment is:",
                str(client_secret_environment)
            ]))

    def parse_access_token(self):
        self.environment = self.get_environment(self.access_token)
        self.merchant_id = self.get_merchant_id(self.access_token)

    def get_environment(self, credential):
        parts = credential.split("$")
        return Environment.All.get(parts[1])

    def get_merchant_id(self, credential):
        parts = credential.split("$")
        return parts[2]
