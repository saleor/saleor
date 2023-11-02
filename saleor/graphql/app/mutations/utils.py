from typing import Optional

from django.core.exceptions import ValidationError

from ....app.error_codes import AppErrorCode
from ....app.models import App


def app_is_not_removed(app: Optional[App], app_global_id: str, field_name: str):
    if app and app.to_remove is True:
        code = AppErrorCode.NOT_FOUND.value
        raise ValidationError(
            {
                field_name: ValidationError(
                    f"Couldn't resolve to a node: {app_global_id}", code=code
                )
            }
        )
