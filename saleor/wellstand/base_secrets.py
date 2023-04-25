class SecretManager:
    def get_secret(self, secret_key: str) -> dict:
        """
        Retrieves a configuration value from the underlying configuration store.
        be set of the format "{os.environ['ENVIRONMENT_NAME']}-{secret_key}"

        :param secret_key: the key of the secret to retrieve

        :return: a dictionary of the configuration for the key
        """
        raise NotImplementedError("get_secret must be implemented by a subclass")
