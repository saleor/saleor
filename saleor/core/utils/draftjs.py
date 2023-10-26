def json_content_to_raw_text(content: dict[str, dict], sep: str = "\n") -> str:
    """Convert DraftJS JSON content to plain text."""

    if not isinstance(content, dict) or "blocks" not in content:
        return ""

    blocks = []
    for block in content["blocks"]:
        block_text = block.get("text", None).strip()
        if block_text is not None:
            blocks.append(block_text)

    return sep.join(blocks)
