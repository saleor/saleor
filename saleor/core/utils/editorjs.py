import re
import warnings
from typing import Dict, List, Literal, Union, overload

from django.utils.html import strip_tags
from urllib3.util import parse_url

BLACKLISTED_URL_SCHEMES = ("javascript",)
HYPERLINK_TAG_WITH_URL_PATTERN = r"(.*?<a\s+href=\\?\")(\w+://\S+[^\\])(\\?\">)"

ITEM_TYPE_TO_CLEAN_FUNC_MAP = {
    "list": lambda *params: clean_list_item(*params),
    "image": lambda *params: clean_image_item(*params),
    "embed": lambda *params: clean_embed_item(*params),
}


@overload
def clean_editor_js(
    definitions: Union[Dict, str, None], *, to_string: Literal[True]
) -> str:
    ...


@overload
def clean_editor_js(definitions: Dict) -> Dict:
    ...


@overload
def clean_editor_js(definitions: None) -> None:
    ...


def clean_editor_js(definitions, *, to_string=False) -> Union[Dict, str, None]:
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

    plain_text_list: List[str] = []

    for index, block in enumerate(blocks):
        block_type = block["type"]
        data = block.get("data")
        if not data or not isinstance(data, dict):
            continue

        params = [blocks, block, plain_text_list, to_string, index]
        if clean_func := ITEM_TYPE_TO_CLEAN_FUNC_MAP.get(block_type):
            clean_func(*params)
        else:
            clean_other_items(*params)

    return " ".join(plain_text_list) if to_string else definitions


def clean_list_item(blocks, block, plain_text_list, to_string, index):
    for item_index, item in enumerate(block["data"]["items"]):
        if not item:
            return
        new_text = clean_text_data(item)
        if to_string:
            plain_text_list.append(strip_tags(new_text))
        else:
            blocks[index]["data"]["items"][item_index] = new_text


def clean_image_item(blocks, block, plain_text_list, to_string, index):
    file_url = block["data"].get("file", {}).get("url")
    caption = block["data"].get("caption")
    if file_url:
        file_url = clean_text_data(file_url)
        if to_string:
            plain_text_list.append(strip_tags(file_url))
        else:
            blocks[index]["data"]["file"]["ulr"] = file_url
    if caption:
        caption = clean_text_data(caption)
        if to_string:
            plain_text_list.append(strip_tags(caption))
        else:
            blocks[index]["data"]["caption"] = caption


def clean_embed_item(blocks, block, plain_text_list, to_string, index):
    for field in ["source", "embed", "caption"]:
        data = block["data"].get(field)
        if not data:
            return
        data = clean_text_data(data)
        if to_string:
            plain_text_list.append(strip_tags(data))
        else:
            blocks[index]["data"][field] = data


def clean_other_items(blocks, block, plain_text_list, to_string, index):
    text = block["data"].get("text")
    if not text:
        return
    new_text = clean_text_data(text)
    if to_string:
        plain_text_list.append(strip_tags(new_text))
    else:
        blocks[index]["data"]["text"] = new_text


def clean_text_data(text: str) -> str:
    """Look for url in text, check if URL is allowed and return the cleaned URL.

    By default, only the protocol ``javascript`` is denied.
    """

    if not text:
        return text

    end_of_match = 0
    new_text = ""
    for match in re.finditer(HYPERLINK_TAG_WITH_URL_PATTERN, text):
        original_url = match.group(2)
        original_url.strip()

        url = parse_url(original_url)
        new_url = url.url
        url_scheme = url.scheme
        if url_scheme in BLACKLISTED_URL_SCHEMES:
            warnings.warn(
                f"An invalid url was sent: {original_url} "
                f"-- Scheme: {url_scheme} is blacklisted"
            )
            new_url = "#invalid"

        new_text += match.group(1) + new_url + match.group(3)
        end_of_match = match.end()

    if end_of_match:
        new_text += text[end_of_match:]

    return new_text if new_text else text
