import os

import dj_database_url
import pytest
from django.conf import settings

pytest_plugins = [
    "saleor.tests.fixtures",
    "saleor.plugins.tests.fixtures",
    "saleor.graphql.tests.fixtures",
    "saleor.graphql.channel.tests.fixtures",
    "saleor.graphql.account.tests.benchmark.fixtures",
    "saleor.graphql.order.tests.benchmark.fixtures",
    "saleor.graphql.giftcard.tests.benchmark.fixtures",
    "saleor.graphql.webhook.tests.benchmark.fixtures",
    "saleor.plugins.webhook.tests.subscription_webhooks.fixtures",
]

if os.environ.get("PYTEST_DB_URL"):

    @pytest.fixture(scope="session")
    def django_db_setup():
        settings.DATABASES = {
            settings.DATABASE_CONNECTION_DEFAULT_NAME: dj_database_url.config(
                env="PYTEST_DB_URL", conn_max_age=600
            ),
        }
