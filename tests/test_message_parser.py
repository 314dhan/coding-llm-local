from message_bubble import parse_message_blocks


def test_plain_text_only():
    blocks = parse_message_blocks("Hello world")
    assert blocks == [{"type": "text", "content": "Hello world"}]


def test_single_code_block():
    text = "Use this:\n```python\nprint('hi')\n```\nDone."
    blocks = parse_message_blocks(text)
    assert len(blocks) == 3
    assert blocks[0] == {"type": "text", "content": "Use this:"}
    assert blocks[1] == {"type": "code", "content": "print('hi')", "lang": "python"}
    assert blocks[2] == {"type": "text", "content": "Done."}


def test_code_block_no_lang():
    blocks = parse_message_blocks("```\nx = 1\n```")
    assert blocks == [{"type": "code", "content": "x = 1", "lang": "text"}]


def test_empty_string():
    assert parse_message_blocks("") == []


def test_multiple_code_blocks():
    text = "First:\n```py\na = 1\n```\nSecond:\n```js\nconsole.log(1)\n```"
    blocks = parse_message_blocks(text)
    assert len(blocks) == 4
    assert blocks[1]["lang"] == "py"
    assert blocks[3]["lang"] == "js"


def test_ignores_empty_text_segments():
    blocks = parse_message_blocks("```python\ncode\n```")
    assert len(blocks) == 1
    assert blocks[0]["type"] == "code"


def test_strips_surrounding_whitespace():
    blocks = parse_message_blocks("  hello  ")
    assert blocks[0]["content"] == "hello"
