import warnings
from typing import Any, Literal, TypedDict, cast, overload

import nh3
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.html import strip_tags
from urllib3.util import parse_url

from ..cleaners.urls import URL_SCHEME_CLEANERS, URLCleanerError

# An allow list that lists the supported block types for ``clean_text_items()``
# We return an error when the type is not part of the allow list
# as a safety measure.
#
# Note: we only support the types that the Saleor Dashboard implements;
#       they are listed here: https://github.com/saleor/saleor-dashboard/blob/2b2311eb2a0a98567efbbe5eef5c3daf66eeeb92/pnpm-lock.yaml#L38-L49
ALLOWED_TEXT_BLOCK_TYPES = ("paragraph", "header", "quote")

ITEM_TYPE_TO_CLEAN_FUNC_MAP = {
    "image": lambda *params: clean_image_item(*params),
    "embed": lambda *params: clean_embed_item(*params),
    "quote": lambda *params: clean_quote_item(*params),
}

ALLOWED_URL_SCHEMES = {
    # WARNING: do NOT add new schemes in directly to this list, only HTTP and HTTPS
    #          should be listed as they are cleaned by urllib3. Instead, add it to
    #          URL_SCHEME_CLEANERS and implement a cleaner that (at minimum) quotes
    #          special characters like "'<> and ASCII control characters
    #          (use urllib.util.parse.quote())
    "http",
    "https",
    *URL_SCHEME_CLEANERS.keys(),
}


def maybe_to_int(o: Any, *, name: str) -> int:
    """Cast a given object to an integer if it's possible, otherwise it raises.

    It's a lenient parsing for backward compatibility.
    """

    if isinstance(o, str):
        if o.isnumeric() is False:
            raise ValidationError(f"{name} must be an integer")
        return int(o)

    if isinstance(o, int) is False:
        raise ValidationError(f"{name} must be an integer")

    return o


class NestedListItemType(TypedDict):
    """The EditorJS inner items of a nested list.

    Example:
        {
            "type" : "list",
            "data" : {
                "style": "ordered",
                "meta": {
                    "start": 2,
                    "counterType": "upper-roman",
                },
                "items" : [
                    {                              # <---
                        "content": "Apples",       # <---
                        "meta": {},                # <---
                        "items": [                 # <---
                            {
                                "content": "Red",
                                "meta": {},
                                "items": []
                            },
                        ]
                    },
                ]
            }
        }

    """

    content: str  # The text
    meta: dict
    items: list["NestedListItemType"]


class NestedListBlockType(TypedDict):
    """The EditorJS outer block of a nested list.

    Example:
        {
            "type" : "list",
            "data" : {
                "style": "ordered",                 # <---
                "meta": {                           # <---
                    "start": 2,                     # <---
                    "counterType": "upper-roman",   # <---
                },                                  # <---
                "items" : [                         # <---
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
                    },
                ]
            }
        }

    """

    style: str
    meta: dict
    items: list["NestedListItemType"]


@overload
def clean_editor_js(
    definitions: dict | str | None, *, to_string: Literal[True]
) -> str: ...


@overload
def clean_editor_js(definitions: dict) -> dict: ...


@overload
def clean_editor_js(definitions: None) -> None: ...


def clean_editor_js(definitions, *, to_string=False) -> dict | str | None:
    """Sanitize a given EditorJS JSON definitions.

    Look for not allowed URLs, replaced them with `invalid` value, and clean valid ones.

    `to_string` flag is used for returning concatenated string from all blocks
     instead of returning json object.
    """
    if definitions is None:
        return "" if to_string else definitions

    blocks = definitions.get("blocks")

    if not blocks or not isinstance(blocks, list):
        return "" if to_string else definitions

    plain_text_list: list[str] = []

    for index, block in enumerate(blocks):
        block_type = block.get("type")

        if not block_type or isinstance(block_type, str) is False:
            raise ValidationError("Missing required key: 'type'")

        data = block.get("data")
        if not data or not isinstance(data, dict):
            continue

        params = [blocks, block, plain_text_list, to_string, index]
        if clean_func := ITEM_TYPE_TO_CLEAN_FUNC_MAP.get(block_type):
            for field in ("width", "height"):
                if (field_value := data.get(field)) is not None:
                    data[field] = maybe_to_int(field_value, name=field)
            clean_func(*params)
        elif block_type == "list":
            clean_list_item(
                block=block,
                to_string=to_string,
                plain_text_list=plain_text_list,
                max_depth=settings.EDITOR_JS_LISTS_MAX_DEPTH,
            )
        else:
            clean_text_items(*params, block_type=block_type)

    return " ".join(plain_text_list) if to_string else definitions


def clean_legacy_list(items: list[str], *, to_string: bool, plain_text_list: list[str]):
    for item_index, item in enumerate(items):
        if isinstance(item, str) is False:
            # Mixing types or version (legacy vs new lists) isn't allowed by Saleor,
            # nor by EditorJS.
            raise ValidationError("Invalid EditorJS list: items must be strings")

        if to_string:
            # Only appends the text if it's not empty as we do a `' '.join(...)`
            # i.e., otherwise it will create unneeded (and ugly) whitespaces.
            if item:
                plain_text_list.append(strip_tags(item))
        else:
            new_text = clean_text_data_block(item)
            items[item_index] = new_text


def clean_meta_block(block: NestedListItemType | dict) -> None:
    """Clean the meta property of a given block.

    Args:
        block: the EditorJS block to clean which contains (or may contain) the 'meta' key
               at the root of the object.

    """

    key_count = 0

    meta = block.get("meta") or {}
    if isinstance(meta, (dict)) is False:
        raise ValidationError(
            "Invalid meta block for EditorJS: meta property must be an object"
        )

    for k, v in meta.items():
        # Validate the key
        if isinstance(k, str) is False:
            raise ValidationError(
                "Invalid property for a meta member for EditorJS: must a string"
            )

        # Validate the value
        if isinstance(v, str):
            meta[k] = clean_text_data_block(v)
        elif isinstance(v, int | float | bool) is False and v is not None:
            raise ValidationError(
                "Invalid meta block for EditorJS: value of a meta must either "
                "a string, an integer, or a float"
            )

        # Stop processing if an excessive key count is found
        key_count += 1
        if key_count > 10:
            raise ValidationError("Invalid meta block for EditorJS: too many fields")


def clean_nested_list(
    items: list[NestedListItemType],
    *,
    current_depth: int,
    max_depth: int,
    to_string: bool,
    plain_text_list: list[str],
):
    # Note: this already validated by ``clean_list_item()`` however, we still need
    #       to perform this check as we are doing recursive checks which thus weren't
    #       checked yet.
    if isinstance(items, list) is False:
        raise ValidationError("Invalid EditorJS list: items must be inside an array")

    if current_depth > max_depth:
        raise ValidationError("Invalid EditorJS list: maximum nesting level exceeeded")

    for item in items:
        if isinstance(item, dict) is False:
            # Mixing types or version (legacy vs new lists) isn't allowed by Saleor,
            # nor by EditorJS.
            raise ValidationError("Invalid EditorJS list: items must be objects")

        text = item.get("content", "")
        if isinstance(text, str) is False:
            raise ValidationError(
                "Invalid EditorJS list: the text contents must be a string"
            )

        if to_string:
            # Only append the text if it's not empty as we do a `' '.join(...)`
            # i.e., otherwise it will create unneeded (and ugly) whitespaces.
            if text:
                plain_text_list.append(strip_tags(text))
        else:
            item["content"] = clean_text_data_block(text)
            clean_meta_block(item)

        # Cleans the children (if any)
        clean_nested_list(
            items=item.get("items", []),
            current_depth=current_depth + 1,
            max_depth=max_depth,
            to_string=to_string,
            plain_text_list=plain_text_list,
        )


def clean_list_item(
    block: dict,
    plain_text_list,
    to_string: bool,
    *,
    max_depth: int,
):
    """Clean EditorJS lists, both legacy (non-nested) and the latest format (nested).

    Args:
        blocks: the list of blocks inside the EditorJS data that we are currently
                cleaning.

        block: the block to clean (`type: list`)

        to_string: whether the results should be exported to plaintext instead of
                   EditorJS format.

        plain_text_list: array of plaintext values to append into when ``to_string``
                         is set to ``True``.

        index: the block's position in the ``blocks`` array.

        max_depth: the maximum level of the list nesting. Limits the amount of recursions
                   done. Must not be set too high (recommended value: 10)

        current_depth: should be set to 0 on the first call, then it gets automatically
                       incremented during the recursive calls in order to keep track of
                       the call depth.

    """

    data = block["data"]
    clean_meta_block(data)

    items = data.get("items", [])
    if isinstance(items, list) is False:
        raise ValidationError("Invalid EditorJS list: items property must be an array")
    items = cast(list, items)

    # Cleans the list style (unordered|ordered|checklist)
    # It's valid both for legacy and new (nested) list formats
    style: None | str
    if style := data.get("style"):
        if isinstance(style, str) is False:
            raise ValidationError(
                "Invalid EditorJS list: style property must be a string"
            )
        data["style"] = clean_text_data_block(style)

    # List empty
    if not items:
        return

    # Looks at the first item to determine whether it's legacy or nested (the new type).
    # We do not do this in a loop as we shouldn't allow users to mix legacy and
    # non-legacy within a block, this isn't valid EditorJS and thus should be rejected
    # by `clean_legacy_list()` and `clean_nested_list()` but this validation is deferred
    # to these functions in order to not iterate multiple times the lists.
    if isinstance(items[0], str):
        # Support for **legacy** lists (https://github.com/editor-js/list-legacy/blob/381254443234ebbec9cc508fa8a7b982b6a79418/README.md#output-data)
        clean_legacy_list(items, to_string=to_string, plain_text_list=plain_text_list)
    elif isinstance(items[0], dict):
        # Support for the new format (nested lists, https://github.com/editor-js/list/blob/f8cde313224499ed5bcf3e93864fc11c45fe7efb/README.md#output-data)
        clean_nested_list(
            items,
            max_depth=max_depth,
            current_depth=0,
            to_string=to_string,
            plain_text_list=plain_text_list,
        )
    else:
        raise ValidationError(
            "Invalid EditorJS list: items must be either a string or an object"
        )


def clean_image_item(blocks, block, plain_text_list, to_string, index):
    data = block["data"]

    for obj in (
        # data.file.url -> support for newer versions of Edjs (2.x)
        data.get("file", {}),
        # data.url -> support for older version (1.x)
        data,
    ):
        if file_url := obj.get("url"):
            if to_string:
                plain_text_list.append(strip_tags(file_url))
            else:
                file_url = clean_url(file_url)
                obj["url"] = file_url

    if caption := data.get("caption"):
        if to_string:
            plain_text_list.append(strip_tags(caption))
        else:
            caption = clean_text_data_block(caption)
            data["caption"] = caption


def clean_embed_item(blocks, block, plain_text_list, to_string, index):
    for field in ["source", "embed"]:
        data = block["data"].get(field)
        if not data:
            continue
        if to_string:
            plain_text_list.append(strip_tags(data))
        else:
            data = clean_url(data)
            blocks[index]["data"][field] = data

    caption = block["data"].get("caption")
    if caption:
        if to_string:
            plain_text_list.append(strip_tags(caption))
        else:
            blocks[index]["data"]["caption"] = clean_text_data_block(caption)

    if service := block["data"].get("service"):
        block["data"]["service"] = clean_text_data_block(service)


def clean_quote_item(blocks, block, plain_text_list, to_string, index):
    """Clean a EditorJS `quote` block.

    Follows the specs from https://github.com/editor-js/quote/blob/78f70cf2391cc8aaf2d2e59615de3ad833d180c3/README.md#output-data
    """

    # Cleans all EditorJS fields from the data block
    for field in ["text", "caption", "alignment", "align"]:
        data = block["data"].get(field)
        if not data:
            continue
        blocks[index]["data"][field] = clean_text_data_block(data)

    if text := block["data"].get("text"):
        plain_text_list.append(strip_tags(text))


def clean_text_items(
    blocks,
    block,
    plain_text_list,
    to_string,
    index,
    *,
    block_type: str,
):
    if block_type not in ALLOWED_TEXT_BLOCK_TYPES:
        raise ValidationError(f"Unsupported block type: {block_type!r}")

    data = block["data"]

    text = data.get("text")
    if text:
        if to_string:
            plain_text_list.append(strip_tags(text))
        else:
            new_text = clean_text_data_block(text)
            data["text"] = new_text

    for field in ("alignment", "align"):
        if value := data.get(field):
            data[field] = clean_text_data_block(value)

    if heading_level := data.get("level"):
        data["level"] = maybe_to_int(heading_level, name="Heading level")


def clean_text_data_block(text: str) -> str:
    """Sanitize the text using nh3 to remove malicious tags and attributes."""
    if not text:
        return text

    return nh3.clean(
        text,
        url_schemes=ALLOWED_URL_SCHEMES | settings.HTML_CLEANER_PREFS.allowed_schemes,
        attributes=settings.HTML_CLEANER_PREFS.allowed_attributes,
        tag_attribute_values=settings.HTML_CLEANER_PREFS.allowed_attribute_values,
        link_rel=settings.HTML_CLEANER_PREFS.link_rel,
    )


def clean_url(dirty_url: str) -> str:
    """Check if URL scheme is allowed."""
    if not dirty_url:
        return ""

    try:
        parsed_url = parse_url(dirty_url.strip())
    except ValueError:
        parsed_url = None

    if (
        parsed_url is None
        or parsed_url.scheme
        not in ALLOWED_URL_SCHEMES | settings.HTML_CLEANER_PREFS.allowed_schemes
    ):
        warnings.warn(
            f"An invalid url or disallowed URL was sent: {dirty_url}",
            stacklevel=3,
        )
        return "#invalid"

    # If the scheme is HTTP(S), then urllib3 already took care of normalization
    # and thus quoted everything that should be quoted (such as dangerous characters
    # like `"`)
    # See https://github.com/urllib3/urllib3/blob/bd37a23af4552548f55d3c723fcb604f9a4983ca/src/urllib3/util/url.py#L415-L446
    if parsed_url.scheme in ("https", "http"):
        return parsed_url.url

    url_cleaner = URL_SCHEME_CLEANERS.get(parsed_url.scheme, None)

    if url_cleaner is None:
        if parsed_url.scheme in settings.HTML_CLEANER_PREFS.allowed_schemes:
            # Deprecated: this is only for backward compatibility - it doesn't define
            #             a cleaner which is dangerous.
            return dirty_url
        # NOTE: this exception should never happen unless a maintainer didn't read the
        #       comment in ALLOWED_URL_SCHEMES
        raise KeyError("No URL cleaner defined", parsed_url.scheme)

    try:
        return url_cleaner(dirty_url=dirty_url)
    except URLCleanerError as exc:
        # Note: InvalidUsage must NOT be handled (should return "Internal Error")
        #       it indicates a code bug if it's raised
        raise ValidationError(str(exc)) from exc
    except ValueError as exc:
        # Note: we do not do str(exc) as may reveal sensitive information
        raise ValidationError("Invalid URL") from exc
