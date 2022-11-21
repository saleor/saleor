import re
import warnings
from typing import Dict, Optional

from django.utils.html import strip_tags
from urllib3.util import parse_url

BLACKLISTED_URL_SCHEMES = ("javascript",)
HYPERLINK_TAG_WITH_URL_PATTERN = r"(.*?<a\s+href=\\?\")(\w+://\S+[^\\])(\\?\">)"


def clean_editor_js(definitions: Optional[Dict], *, to_string: bool = False):
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

    plain_text_list = []

    for index, block in enumerate(blocks):
        block_type = block["type"]
        data = block.get("data")
        if not data or not isinstance(data, dict):
            continue

        if block_type == "list":
            for item_index, item in enumerate(block["data"]["items"]):
                if not item:
                    continue
                new_text = clean_text_data(item)
                if to_string:
                    plain_text_list.append(strip_tags(new_text))
                else:
                    blocks[index]["data"]["items"][item_index] = new_text
        else:
            text = block["data"].get("text")
            if not text:
                continue
            new_text = clean_text_data(text)
            if to_string:
                plain_text_list.append(strip_tags(new_text))
            else:
                blocks[index]["data"]["text"] = new_text

    return " ".join(plain_text_list) if to_string else definitions


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
        url_scheme = url.scheme  # type: ignore
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
