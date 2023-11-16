import os
import json

from google.cloud import secretmanager_v1

from cachetools import cached
from saleor.pharmacy.base_secrets import SecretManager
from saleor.pharmacy import cache


class GoogleSecretManager(SecretManager):
    """
    Implements a SecretManager that uses the Google Secret Manager to get secrets.

    Requires the GOOGLE_APPLICATION_CREDENTIALS environment variable to be set to the path of the service account json
    file when developing locally.  The service account needs to have 'Secret Manager Secret Accessor' role at a minimum.
    The service account json file can be downloaded from the Google Cloud Console.

    When running in Kubernetes, the service account being used needs to have Editor
    permissions.
    """

    def __init__(self):
        super().__init__()
        self.client = secretmanager_v1.SecretManagerServiceClient()
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT")

    @staticmethod
    @cached(cache)
    def get_secret(secret_key: str) -> dict:
        env_name = os.environ["ENVIRONMENT_NAME"]
        google_project = os.environ["GOOGLE_PROJECT_NAME"]

        client = secretmanager_v1.SecretManagerServiceClient()

        name = client.secret_version_path(
            google_project, f"{env_name}-{secret_key}", "latest"
        )
        response = client.access_secret_version(name=name)
        return json.loads(response.payload.data)

    @staticmethod
    @cached(cache)
    def get_secret_single_value(secret_key: str) -> str:
        env_name = os.environ["ENVIRONMENT_NAME"]
        google_project = os.environ["GOOGLE_PROJECT_NAME"]

        client = secretmanager_v1.SecretManagerServiceClient()

        name = client.secret_version_path(
            google_project, f"{env_name}-{secret_key}", "latest"
        )
        response = client.access_secret_version(name=name)
        return response.payload.data.decode("UTF-8")
