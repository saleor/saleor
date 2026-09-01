import pytest
from django.apps import apps


@pytest.mark.parametrize(
    ("_case", "namespace_import"),
    [
        ("unset", None),
        ("valid_import", "saleor.core.db.locks.get_advisory_lock_namespace"),
    ],
)
def test_validate_advisory_lock_namespace_import_passes(
    _case, namespace_import, settings
):
    # given
    settings.ADVISORY_LOCK_NAMESPACE_IMPORT = namespace_import
    app_config = apps.get_app_config("core")

    # when / then
    app_config.validate_advisory_lock_namespace_import()


def test_validate_advisory_lock_namespace_import_rejects_bad_import(settings):
    # given
    settings.ADVISORY_LOCK_NAMESPACE_IMPORT = "saleor.nonexistent.module.get_namespace"
    app_config = apps.get_app_config("core")

    # when / then
    with pytest.raises(
        ImportError, match="Failed to import advisory lock namespace function"
    ):
        app_config.validate_advisory_lock_namespace_import()
