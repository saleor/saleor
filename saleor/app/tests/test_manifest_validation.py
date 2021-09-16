from collections import defaultdict

import pytest

from ..manifest_validations import _validate_configuration
from ..types import AppExtensionTarget, AppExtensionType, AppExtensionView


@pytest.mark.parametrize(
    "view, type, target",
    [
        (
            AppExtensionView.PRODUCT,
            AppExtensionType.OVERVIEW,
            AppExtensionTarget.CREATE,
        ),
        (
            AppExtensionView.PRODUCT,
            AppExtensionType.OVERVIEW,
            AppExtensionTarget.MORE_ACTIONS,
        ),
        (AppExtensionView.PRODUCT, AppExtensionType.DETAILS, AppExtensionTarget.CREATE),
        (
            AppExtensionView.PRODUCT,
            AppExtensionType.DETAILS,
            AppExtensionTarget.MORE_ACTIONS,
        ),
    ],
)
def test_validate_configuration_accepts_correct_configuration(view, type, target):
    errors = []
    extension = {
        "view": view,
        "type": type,
        "target": target,
    }
    _validate_configuration(extension, errors)

    assert not errors


def test_incorrect_configuration():
    errors = defaultdict(list)
    extension = {
        "view": AppExtensionView.PRODUCT,
        "type": AppExtensionType.DETAILS,
        "target": "incorrect",
    }
    _validate_configuration(extension, errors)

    assert len(errors["extensions"]) == 1
