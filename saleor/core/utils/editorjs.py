from typing import Literal, overload

from ..editorjs import editorjs_to_text, parse_editorjs


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

    if to_string is True:
        return editorjs_to_text(definitions)
    return parse_editorjs(definitions).model_dump()
