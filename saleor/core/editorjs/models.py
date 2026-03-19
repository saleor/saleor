from typing import Annotated, Literal, Union

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.html import strip_tags
from pydantic import (
    AfterValidator,
    BeforeValidator,
    ConfigDict,
    Field,
)
from pydantic import (
    BaseModel as UnsafeBaseModel,
)

from .cleaners import (
    _clean_legacy_list_items,
    _clean_meta_dict,
    _clean_text,
    _clean_url_value,
)

# Note: for ``Text`` we use AfterValidator to ensure type stability
#       otherwise we may end up getting other types than ``str | None``
Text = Annotated[str, AfterValidator(_clean_text)]
URL = Annotated[str, BeforeValidator(_clean_url_value)]

MetaValue = int | float | bool | Text | None
MetaDict = Annotated[dict[Text, MetaValue], AfterValidator(_clean_meta_dict)]
ListItem = Union["EditorJSNestedListItemModel", Text]
ListItems = Annotated[
    list[ListItem] | None,
    BeforeValidator(_clean_legacy_list_items),
]
ListStyle = Annotated[
    Literal["ordered", "unordered", "checklist"] | None,
    BeforeValidator(_clean_text),
]


class StrictBaseModel(UnsafeBaseModel):
    """Strict version of the pydantic BaseModel.

    Forbids any extra field - extra fields could be a XSS vector due to not
    being cleaned or assessed. For example, upgrading the EditorJS client-side
    library could lead to new fields being added (thus opening new XSS holes),
    as well some unofficial client-side libraries add custom (non-official) fields
    which could be exploited.
    """

    model_config = ConfigDict(extra="forbid")


class EditorJSBlock(StrictBaseModel):
    """Defines a base EditorJS block."""

    def to_text(self) -> str:
        """Convert the block into a plaintext form."""
        raise NotImplementedError


class EditorJSParagraphDataModel(StrictBaseModel):
    """Match the data payload for an EditorJS paragraph block.

    Example:
        {
            "text": "Hello"
        }

    """

    text: Text | None = None
    alignment: Text | None = None
    align: Text | None = None


class EditorJSHeaderDataModel(StrictBaseModel):
    """Match the data payload for an EditorJS header block.

    Example:
        {
            "text": "Title",
            "level": 2
        }

    """

    text: Text | None = None
    level: int | Text | None = None
    alignment: Text | None = None
    align: Text | None = None


class EditorJSQuoteDataModel(StrictBaseModel):
    """Match the data payload for an EditorJS quote block.

    Example:
        {
            "text": "Quote",
            "caption": "Author"
        }

    """

    text: Text | None = None
    caption: Text | None = None
    alignment: Text | None = None
    align: Text | None = None


class EditorJSEmbedDataModel(StrictBaseModel):
    """Match the data payload for an EditorJS embed block.

    Example:
        {
            "embed": "https://www.youtube.com/embed/dQw4w9WgXcQ",
            "source": "https://youtu.be/dQw4w9WgXcQ"
        }

    """

    embed: URL | None = None
    source: URL | None = None
    caption: Text | None = None
    service: Text | None = None
    width: int | float | None = None
    height: int | float | None = None


class EditorJSNestedListItemModel(StrictBaseModel):
    """Match an EditorJS nested list item object.

    Example:
        {
            "content": "Apples",
            "items": [
                {
                    "content": "Apples",
                    "meta": {},
                    "items": [
                        {
                            "content": "Red",
                            "meta": {},
                            "items": []
                        },
                    ]
                }
            ],
            "meta": {}
        }

    """

    content: Text
    items: list["EditorJSNestedListItemModel"] = Field(default_factory=list)
    meta: MetaDict = Field(default_factory=dict)


class EditorJSListDataModel(StrictBaseModel):
    """Match the data payload for an EditorJS list block.

    It encapsulates both legacy (flat lists) and nested (newer) format.

    Example:
        {
            "style": "unordered",
            "items": [
                "One"
            ]
        }

    """

    style: ListStyle = None
    items: ListItems = None
    meta: MetaDict = Field(default_factory=dict)

    def to_text(
        self,
        node: ListItem,
        *,
        current_depth: int,
        max_depth: int,
    ) -> str:
        # TODO: depth validation shouldn't only happen in to_text
        if current_depth > max_depth:
            raise ValidationError(
                "Invalid EditorJS list: maximum nesting level exceeeded"
            )

        if isinstance(node, str):
            return strip_tags(node)

        parts = []

        for item in node.items:
            if isinstance(item, EditorJSNestedListItemModel):
                if item.content:
                    parts.append(item.content)
                if part := self.to_text(
                    item, current_depth=current_depth + 1, max_depth=max_depth
                ):
                    parts.append(part)
            elif isinstance(item, str):
                parts.append(strip_tags(item))
            else:
                raise TypeError(f"Unexpected list member type: {item!r}")

        return " ".join(parts)


class EditorJSParagraphBlockModel(EditorJSBlock):
    """Match an EditorJS paragraph block object.

    Example:
        {
            "type": "paragraph",
            "data": {
                "text": "Hello"
            }
        }

    """

    type: Literal["paragraph"]
    data: EditorJSParagraphDataModel
    id: Text | None = None

    def to_text(self) -> str:
        return self.data.text or ""


class EditorJSHeaderBlockModel(EditorJSBlock):
    """Match an EditorJS header block object.

    Example:
        {
            "type": "header",
            "data": {
                "text": "Title",
                "level": 2
            }
        }

    """

    type: Literal["header"]
    data: EditorJSHeaderDataModel
    id: Text | None = None

    def to_text(self) -> str:
        return self.data.text or ""


class EditorJSListBlockModel(EditorJSBlock):
    """Match an EditorJS list block object.

    Example:
        {
            "type": "list",
            "data": {
                "style": "unordered",
                "items": [
                    "One"
                ]
            }
        }

    """

    type: Literal["list"]
    data: EditorJSListDataModel
    id: Text | None = None

    def to_text(self) -> str:
        if not self.data.items:
            return ""

        text = ""
        for item in self.data.items:
            if text:
                text += " "
            text += self.data.to_text(
                node=item,
                current_depth=0,
                max_depth=settings.EDITOR_JS_LISTS_MAX_DEPTH,
            )
        return text


class EditorJSQuoteBlockModel(EditorJSBlock):
    """Match an EditorJS quote block object.

    Example:
        {
            "type": "quote",
            "data": {
                "text": "Quote",
                "caption": "Author"
            }
        }

    """

    type: Literal["quote"]
    data: EditorJSQuoteDataModel
    id: Text | None = None

    def to_text(self) -> str:
        return self.data.text or ""


class EditorJSEmbedBlockModel(EditorJSBlock):
    """Match an EditorJS embed block object.

    Example:
        {
            "type": "embed",
            "data": {
                "embed": "https://www.youtube.com/embed/dQw4w9WgXcQ",
                "source": "https://youtu.be/dQw4w9WgXcQ"
            }
        }

    """

    type: Literal["embed"]
    data: EditorJSEmbedDataModel
    id: Text | None = None

    def to_text(self) -> str:
        text = ""
        for field in ("source", "embed", "caption"):
            if value := getattr(self.data, field, None):
                sep = "" if not text else " "
                text += f"{sep}{value}"
        return text


EditorJSBlockModel = Annotated[
    EditorJSParagraphBlockModel
    | EditorJSHeaderBlockModel
    | EditorJSListBlockModel
    | EditorJSQuoteBlockModel
    | EditorJSEmbedBlockModel,
    Field(discriminator="type"),
]


class EditorJSDocumentModel(StrictBaseModel):
    """Match the root EditorJS document object.

    Example:
        {
            "version": "2.29.0",
            "time": 1710000000000,
            "blocks": []
        }

    """

    version: Text | None = None
    time: int | float | None = None
    blocks: list[EditorJSBlockModel] | None = None


# TODO: tests:
#    - Cannot provide unknown 'type'
#    - Cannot provide extra data
