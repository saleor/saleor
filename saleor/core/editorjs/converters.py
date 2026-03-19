from .models import EditorJSDocumentModel


def parse_editorjs(data: dict) -> EditorJSDocumentModel:
    return EditorJSDocumentModel.model_validate(data)


def editorjs_to_text(data: dict) -> str:
    doc = parse_editorjs(data)

    if not doc.blocks:
        return ""

    text = ""
    sep = ""
    for block in doc.blocks:
        if text:
            sep = " "

        text = f"{sep}{block.to_text()}"
    return text
