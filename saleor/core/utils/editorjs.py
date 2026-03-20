import logging
from typing import Literal, overload

import pydantic_core
from django.core.exceptions import ValidationError

from ..editorjs import clean_editorjs, editorjs_to_text

logger = logging.getLogger(__name__)


@overload
def clean_editor_js(definitions: dict | None, *, to_string: Literal[True]) -> str: ...


@overload
def clean_editor_js(definitions: dict) -> dict: ...


@overload
def clean_editor_js(definitions: None) -> None: ...


def clean_editor_js(definitions: dict | None, *, to_string=False) -> dict | str | None:
    """Sanitize a given EditorJS JSON definitions.

    Look for not allowed URLs, replaced them with `invalid` value, and clean valid ones.

    `to_string` flag is used for returning concatenated string from all blocks
     instead of returning json object.
    """

    if definitions is None:
        return "" if to_string else definitions

    try:
        if to_string is True:
            return editorjs_to_text(definitions)
        return clean_editorjs(definitions)
    except pydantic_core.ValidationError as exc:
        # Needs to be logged because Saleor doesn't log handled errors in GraphQL
        # and we cannot return the error the user as it can reveal internal information
        logger.info("Received invalid EditorJS input: %s", str(exc))
        raise ValidationError("Invalid input EditorJS format") from exc
