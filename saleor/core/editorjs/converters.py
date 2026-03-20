from django.utils.html import strip_tags

from .models import EditorJSDocumentModel


def parse_editorjs(data: dict) -> EditorJSDocumentModel:
    """Parse EditorJS dictionary into a cleaned Pydantic model.

    :raises pydantic.ValidationError: when the input doesn't match the schema/models.
    :raises django.core.exceptions.ValidationError: when Saleor checks don't pass.
    """

    return EditorJSDocumentModel.model_validate(data)


def clean_editorjs(data: dict) -> dict:
    """Return a cleaned version of the EditorJS input."""
    return parse_editorjs(data).model_dump(exclude_unset=True)


def editorjs_to_text(data: dict) -> str:
    """Convert EditorJS blocks into plaintext."""
    doc = parse_editorjs(data)

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
