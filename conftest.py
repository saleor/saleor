import os

import dj_database_url
import django.test
import pytest
from django.conf import settings
from django.core.management import call_command
from django.db import connections
from django.db.backends.postgresql.creation import DatabaseCreation
from django.test.testcases import TransactionTestCase
from django.test.utils import setup_databases, teardown_databases
from pytest_django.fixtures import (
    _disable_migrations,
    _get_databases_for_setup,
)

from saleor.db_snapshot.utils import has_snapshot, load_snapshot
from saleor.tests.utils import prepare_test_db_connections

TEST_DATABASES = {
    settings.DATABASE_CONNECTION_DEFAULT_NAME,
    settings.DATABASE_CONNECTION_REPLICA_NAME,
}
# Here, we trick Django test cases into using multiple databases.
# Thanks to this, we do not have to mark all tests
# with @pytest.mark.django_db(databases=['default', 'replica'])
django.test.TransactionTestCase.databases = TEST_DATABASES
django.test.TestCase.databases = TEST_DATABASES

prepare_test_db_connections()

pytest_plugins = [
    "saleor.tests.fixtures",
    "saleor.app.tests.fixtures",
    "saleor.plugins.tests.fixtures",
    "saleor.graphql.tests.fixtures",
    "saleor.webhook.tests.fixtures",
    "saleor.tax.tests.fixtures",
    "saleor.channel.tests.fixtures",
    "saleor.page.tests.fixtures",
    "saleor.menu.tests.fixtures",
    "saleor.warehouse.tests.fixtures",
    "saleor.thumbnail.tests.fixtures",
    "saleor.order.tests.fixtures",
    "saleor.product.tests.fixtures",
    "saleor.site.tests.fixtures",
    "saleor.shipping.tests.fixtures",
    "saleor.permission.tests.fixtures",
    "saleor.giftcard.tests.fixtures",
    "saleor.discount.tests.fixtures",
    "saleor.checkout.tests.fixtures",
    "saleor.attribute.tests.fixtures",
    "saleor.account.tests.fixtures",
    "saleor.graphql.account.tests.fixtures",
    "saleor.payment.tests.fixtures",
    "saleor.webhook.tests.circuit_breaker.fixtures",
]


def pytest_addoption(parser):
    parser.addoption(
        "--run-slow",
        action="store_true",
        default=False,
        help="Run tests marked as slow.",
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: mark test as slow")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-slow"):
        return

    skip_slow = pytest.mark.skip(
        reason="test is marked as slow and --run-slow is not passed"
    )

    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)


if not os.environ.get("PYTEST_DB_URL"):

    def _install_snapshot_hook():
        """Abc.

        Monkey-patch Django's _create_test_db to load the snapshot SQL right
        after the empty test database is created.  When Django's create_test_db
        subsequently calls ``migrate``, it will see the 1,300+ snapshot
        migrations already recorded in django_migrations and only apply the
        ~54 newer ones.
        """

        _original = DatabaseCreation._create_test_db

        def _create_test_db_with_snapshot(self, verbosity, autoclobber, keepdb):
            result = _original(self, verbosity, autoclobber, keepdb)
            # After CREATE DATABASE, point the connection at the new test DB
            # and load the snapshot before Django runs migrate.
            test_db_name = self._get_test_db_name()
            old_name = self.connection.settings_dict["NAME"]
            self.connection.close()
            self.connection.settings_dict["NAME"] = test_db_name
            try:
                load_snapshot(self.connection)
            finally:
                # Restore — create_test_db will set the name again itself.
                self.connection.close()
                self.connection.settings_dict["NAME"] = old_name
            return result

        DatabaseCreation._create_test_db = _create_test_db_with_snapshot

    @pytest.fixture(scope="session")
    def django_db_setup(
        request,
        django_test_environment,
        django_db_blocker,
        django_db_use_migrations,
        django_db_keepdb,
        django_db_createdb,
        django_db_modify_db_settings,
    ):
        """Use DB snapshot for fresh test databases to skip old migrations."""

        setup_databases_args = {}
        keepdb = django_db_keepdb and not django_db_createdb
        use_snapshot = has_snapshot() and django_db_use_migrations

        if not django_db_use_migrations:
            _disable_migrations()

        if keepdb:
            setup_databases_args["keepdb"] = True

        # When snapshot is available, hook into DB creation so the snapshot
        # is loaded right after CREATE DATABASE but before migrate runs.
        if use_snapshot and not keepdb:
            _install_snapshot_hook()

        aliases, serialized_aliases = _get_databases_for_setup(request.session.items)

        with django_db_blocker.unblock():
            db_cfg = setup_databases(
                verbosity=request.config.option.verbose,
                interactive=False,
                aliases=aliases,
                serialized_aliases=serialized_aliases,
                **setup_databases_args,
            )

        yield

        if not keepdb:
            with django_db_blocker.unblock():
                try:
                    teardown_databases(db_cfg, verbosity=request.config.option.verbose)
                except Exception as exc:
                    request.node.warn(
                        pytest.PytestWarning(
                            f"Error when trying to teardown test databases: {exc!r}"
                        )
                    )


elif os.environ.get("PYTEST_DB_URL"):

    @pytest.fixture(scope="session")
    def django_db_setup():  # noqa: PT004
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
