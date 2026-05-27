import re


def parse_message_blocks(text: str) -> list[dict]:
    """Split a message into alternating text and fenced code blocks.

    Returns list of dicts:
        {"type": "text", "content": str}
        {"type": "code", "content": str, "lang": str}
    """
    if not text:
        return []

    blocks: list[dict] = []
    pattern = re.compile(r"```(\w*)\n(.*?)```", re.DOTALL)
    last_end = 0

    for match in pattern.finditer(text):
        before = text[last_end:match.start()].strip()
        if before:
            blocks.append({"type": "text", "content": before})
        lang = match.group(1).strip() or "text"
        code = match.group(2).rstrip("\n")
        blocks.append({"type": "code", "content": code, "lang": lang})
        last_end = match.end()

    remaining = text[last_end:].strip()
    if remaining:
        blocks.append({"type": "text", "content": remaining})

    return blocks
