import re
import warnings

from urllib3.util import parse_url

BLACKLISTED_URL_SCHEMES = ("javascript",)
HYPERLINK_TAG_WITH_URL_PATTERN = r"(.*?<a\s+href=\\?\")(\w+://\S+[^\\])(\\?\">)"


def clean_editor_js(definitions: dict):
    """Sanitize a given EditorJS JSON definitions.

    Look for not allowed URLs, replaced them with `invalid` value, and clean valid ones.
    """
    blocks = definitions.get("blocks")

    if not blocks or not isinstance(blocks, list):
        return definitions

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
                blocks[index]["data"]["items"][item_index] = new_text
        else:
            text = block["data"]["text"]
            if not text:
                continue
            new_text = clean_text_data(text)

            blocks[index]["data"]["text"] = new_text

    return definitions


def clean_text_data(text: str):
    """Look for url in text, check if URL is allowed and return the cleaned URL.

    By default, only the protocol ``javascript`` is denied.
    """

    if not text:
        return

    end_of_match = 0
    new_text = ""
    for match in re.finditer(HYPERLINK_TAG_WITH_URL_PATTERN, text):
        original_url = match.group(2)
        original_url.strip()

        url = parse_url(original_url)
        new_url = url.url
        if url.scheme in BLACKLISTED_URL_SCHEMES:
            warnings.warn(
                f"An invalid url was sent: {original_url} "
                f"-- Scheme: {url.scheme} is blacklisted"
            )
            new_url = "#invalid"

        new_text += match.group(1) + new_url + match.group(3)
        end_of_match = match.end()

    if end_of_match:
        new_text += text[end_of_match:]

    return new_text if new_text else text
