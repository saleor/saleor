from typing import Annotated, Literal, Union

from django.conf import settings
from django.core.exceptions import ValidationError
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
    _clean_meta_dict,
    _clean_nested_list_items,
    _clean_text,
    _clean_url_value,
)
from .utils import maybe_to_int

# Note: we use AfterValidator to ensure type stability otherwise we may end up
#       getting other types than ``str | None``
Text = Annotated[str, AfterValidator(_clean_text)]
URL = Annotated[str, AfterValidator(_clean_url_value)]

MetaValue = int | float | bool | Text | None
MetaDict = Annotated[dict[Text, MetaValue], AfterValidator(_clean_meta_dict)]
ListItem = Union["EditorJSNestedListItemModel", Text, None]
ListItems = Annotated[
    list[ListItem] | None,
    BeforeValidator(_clean_nested_list_items),
]
ListStyle = Annotated[
    Literal["ordered", "unordered", "checklist"] | None,
    AfterValidator(_clean_text),
]
LineantNumeric = Annotated[int | float, BeforeValidator(maybe_to_int)]


class StrictBaseModel(UnsafeBaseModel):
    """Strict version of the pydantic BaseModel.

    Forbids any extra field - extra fields could be a XSS vector due to not
    being cleaned or assessed. For example, upgrading the EditorJS client-side
    library could lead to new fields being added (thus opening new XSS holes),
    as well some unofficial client-side libraries add custom (non-official) fields
    which could be exploited.
    """

    model_config = ConfigDict(extra="forbid")


class SizeDataModel(StrictBaseModel):
    """An EditorJS ``data`` block that allows to set a size."""

    width: LineantNumeric | None = None
    height: LineantNumeric | None = None


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
    level: LineantNumeric | None = None
    alignment: Text | None = None
    align: Text | None = None


class EditorJSQuoteDataModel(SizeDataModel):
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


class EditorJSEmbedDataModel(SizeDataModel):
    """Match the data payload for an EditorJS embed block.

    Example:
        {
            "embed": "https://www.youtube.com/embed/XXX",
            "source": "https://youtu.be/XXX"
        }

    """

    embed: URL | None = None
    source: URL | None = None
    caption: Text | None = None
    service: Text | None = None


class ImageFileModel(UnsafeBaseModel):
    """Represent ``image.file`` object from EditorJS.

    https://github.com/editor-js/image/blob/d7f0afb5f2e0110dc716941268e6689857a58830/README.md#output-data
    """

    # Drop any unknown field - as per EditorJS specs, the 'image.file' object can
    # contain anything
    # TODO: test case
    model_config = ConfigDict(extra="ignore")

    url: URL | None = None


class EditorJSImageDataModel(SizeDataModel):
    """Match the data payload for an EditorJS image block.

    Example:
        {
            "file": {
                "url" : "https://example.com/image.png"
            },
            "caption" : "my caption",
            "withBorder" : false,
            "withBackground" : false,
            "stretched" : true,
        }

    """

    file: ImageFileModel | None = None
    caption: Text | None = None
    withBorder: bool | None = None
    withBackground: bool | None = None
    stretched: bool | None = None

    # This is invalid but kept for backward compatibility
    # (instead, user should put it in file.url)
    url: URL | None = None


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

    content: Text | None = None
    items: list["EditorJSNestedListItemModel"] = Field(default_factory=list)
    meta: MetaDict | None = Field(default_factory=dict)


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
    meta: MetaDict | None = Field(default_factory=dict)

    def to_text(
        self,
        node: ListItem,
        *,
        current_depth: int,
        max_depth: int,
    ) -> str:
        if current_depth > max_depth:
            raise ValidationError(
                "Invalid EditorJS list: maximum nesting level exceeded"
            )

        if isinstance(node, str):
            return node

        if not node or node.items:
            return ""

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
                if item:
                    parts.append(item)
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
        sep = ""
        for item in self.data.items:
            if text:
                sep = " "
            part = self.data.to_text(
                node=item,
                current_depth=0,
                max_depth=settings.EDITOR_JS_LISTS_MAX_DEPTH,
            )
            if part:
                text += f"{sep}{part}"
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


class EditorJSImageBlockModel(EditorJSBlock):
    """Match an EditorJS image block object.

    Example:
        {
            "type" : "image",
            "data" : {
                "file": {
                    "url" : "https://example.com/image.png"
                },
                "caption" : "my caption",
                "withBorder" : false,
                "withBackground" : false,
                "stretched" : true,
            }
        }

    """

    type: Literal["image"]
    data: EditorJSImageDataModel
    id: Text | None = None

    # This is invalid but kept for backward compatibility
    # (instead, user should put it in data.file.url)
    url: URL | None = None

    def to_text(self) -> str:
        text = ""
        sep = ""
        if self.data.file and (url := self.data.file.url):
            text += f"{sep}{url}"
        if text:
            sep = " "
        if caption := self.data.caption:
            text += f"{sep}{caption}"
        return text


EditorJSBlockModel = Annotated[
    EditorJSParagraphBlockModel
    | EditorJSHeaderBlockModel
    | EditorJSListBlockModel
    | EditorJSQuoteBlockModel
    | EditorJSEmbedBlockModel
    | EditorJSImageBlockModel,
    Field(discriminator="type"),
]


class EditorJSDocumentModel(StrictBaseModel):
    """Match the root EditorJS document object.

    Example:
        {
            "version": "2.29.0",
            "time": 123456789,
            "blocks": []
        }

    """

    version: Text | None = None
    time: int | float | None = None
    blocks: list[EditorJSBlockModel] | None = None


# TODO: tests:
#    - Cannot provide unknown 'type'
#    - Cannot provide extra data
