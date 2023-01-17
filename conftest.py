import os

import dj_database_url
import django.test
import pytest
from django.conf import settings
from django.core.management import call_command
from django.db import connections
from django.test.testcases import TransactionTestCase

pytest_plugins = [
    "saleor.tests.fixtures",
    "saleor.plugins.tests.fixtures",
    "saleor.graphql.tests.fixtures",
    "saleor.graphql.channel.tests.fixtures",
    "saleor.graphql.channel.tests.benchmark.fixtures",
    "saleor.graphql.account.tests.benchmark.fixtures",
    "saleor.graphql.order.tests.benchmark.fixtures",
    "saleor.graphql.giftcard.tests.benchmark.fixtures",
    "saleor.graphql.webhook.tests.benchmark.fixtures",
    "saleor.plugins.webhook.tests.subscription_webhooks.fixtures",
    "saleor.tax.tests.fixtures",
]

if os.environ.get("PYTEST_DB_URL"):

    @pytest.fixture(scope="session")
    def django_db_setup():
        settings.DATABASES = {
            settings.DATABASE_CONNECTION_DEFAULT_NAME: dj_database_url.config(
                env="PYTEST_DB_URL", conn_max_age=600
            ),
        }

    # In case transactional tests are run against a DB that has additional models
    # defined, test cleanup can fail when Django sends TRUNCATE queries for all tables
    # used during tests. It has no idea about this additional model, so it's not
    # included in this query. If this model references any table that is being
    # truncated, query will fail with an error:
    #  django.db.utils.NotSupportedError: cannot truncate a table referenced in a
    #                                     foreign key constraint
    #  DETAIL:  Table "new_table" references "existing_table".
    #  HINT:  Truncate table "new_table" at the same time, or use TRUNCATE ... CASCADE
    class Custom(TransactionTestCase):
        def _fixture_teardown(self):
            for db_name in self._databases_names(include_mirrors=False):  # type: ignore[attr-defined] # raw internals # noqa: E501
                inhibit_post_migrate = self.available_apps is not None or (
                    self.serialized_rollback
                    and hasattr(connections[db_name], "_test_serialized_contents")
                )
                call_command(
                    "flush",
                    verbosity=0,
                    interactive=False,
                    database=db_name,
                    reset_sequences=False,
                    allow_cascade=True,
                    inhibit_post_migrate=inhibit_post_migrate,
                )

    django.test.TransactionTestCase = Custom  # type:ignore[misc]
