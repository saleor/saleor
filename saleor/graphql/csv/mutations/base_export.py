from collections.abc import Mapping
from typing import Union

import graphene
from django.core.exceptions import ValidationError

from ...core.enums import ExportErrorCode
from ...core.mutations import BaseMutation
from ..enums import ExportScope
from ..types import ExportFile


class BaseExportMutation(BaseMutation):
    export_file = graphene.Field(
        ExportFile,
        description=(
            "The newly created export file job which is responsible for export data."
        ),
    )

    class Meta:
        abstract = True

    @classmethod
    def get_scope(cls, input, only_type) -> Mapping[str, Union[list, dict, str]]:
        scope = input["scope"]
        if scope == ExportScope.IDS.value:  # type: ignore[attr-defined] # mypy does not understand graphene enums # noqa: E501
            return cls.clean_ids(input, only_type)
        elif scope == ExportScope.FILTER.value:  # type: ignore[attr-defined] # mypy does not understand graphene enums # noqa: E501
            return cls.clean_filter(input)
        return {"all": ""}

    @classmethod
    def clean_ids(cls, input, only_type) -> dict[str, list[str]]:
        ids = input.get("ids", [])
        if not ids:
            raise ValidationError(
                {
                    "ids": ValidationError(
                        "You must provide at least one id.",
                        code=ExportErrorCode.REQUIRED.value,
                    )
                }
            )
        pks = cls.get_global_ids_or_error(ids, only_type=only_type, field="ids")
        return {"ids": pks}

    @staticmethod
    def clean_filter(input) -> dict[str, dict]:
        filter = input.get("filter")
        if not filter:
            raise ValidationError(
                {
                    "filter": ValidationError(
                        "You must provide filter input.",
                        code=ExportErrorCode.REQUIRED.value,
                    )
                }
            )
        return {"filter": filter}
