import logging
from typing import overload

import pydantic_core
from django.core.exceptions import ValidationError
from django.utils.html import strip_tags

from .models import EditorJSDocumentModel

logger = logging.getLogger(__name__)


def parse_editorjs(data: dict, *, for_django: bool = True) -> EditorJSDocumentModel:
    """Parse EditorJS dictionary into a cleaned Pydantic model.

    :param dict data: the EditorJS data to validate and to clean.
    :param bool for_django: Whether to convert exceptions into something django
        understands. Useful for models and GraphQL as ValidationError is automatically
        handled. `False` should be passed if we want to handle the errors explicitly
        or we need verbosity.
        Can only be raised when ``for_django=False``.
    :raises pydantic.ValidationError: when the input doesn't match the schema/models.
    :raises django.core.exceptions.ValidationError: when Saleor checks don't pass.
    """

    try:
        return EditorJSDocumentModel.model_validate(data)
    except pydantic_core.ValidationError as exc:
        if for_django is True:
            # Needs to be logged because Saleor doesn't log handled errors in GraphQL
            # and we cannot return the error the user as it can reveal internal information
            logger.info("Received invalid EditorJS input: %s", str(exc))
            raise ValidationError("Invalid EditorJS input") from exc
        raise


@overload
def clean_editorjs(data: dict, *, for_django: bool = True) -> dict: ...
@overload
def clean_editorjs(data: None, *, for_django: bool = True) -> None: ...


def clean_editorjs(data: dict | None, *, for_django: bool = True) -> dict | None:
    """Return a cleaned version of the EditorJS input.

    :param dict data: the EditorJS data to validate and to clean.
    :param bool for_django: Whether to convert exceptions into something django
        understands. Useful for models and GraphQL as ValidationError is automatically
        handled. `False` should be passed if we want to handle the errors explicitly
        or we need verbosity.
    :raises pydantic.ValidationError: when the input doesn't match the schema/models.
        Can only be raised when ``for_django=False``.
    :raises django.core.exceptions.ValidationError: when Saleor checks don't pass.
    :return: A **copy** of the input dictionary that was cleaned.
    """

    if data is None:
        return None
    return parse_editorjs(data, for_django=for_django).model_dump(exclude_unset=True)


def editorjs_to_text(data: dict | None, *, for_django: bool = True) -> str:
    """Convert EditorJS blocks into plaintext.

    :param bool for_django: Whether to convert exceptions into something django
        understands. Useful for models and GraphQL as ValidationError is automatically
        handled. `False` should be passed if we want to handle the errors explicitly
        or we need verbosity.
    :raises pydantic.ValidationError: when the input doesn't match the schema/models.
        Can only be raised when ``for_django=False``.
    :raises django.core.exceptions.ValidationError: when Saleor checks don't pass.
    """

    if data is None:
        return ""

    doc = parse_editorjs(data, for_django=for_django)

    if not doc.blocks:
        return ""

    text = ""
    sep = ""
    for block in doc.blocks:
        if text:
            sep = " "

        part = strip_tags(block.to_text())
        if part:
            text += f"{sep}{part}"
    return text
