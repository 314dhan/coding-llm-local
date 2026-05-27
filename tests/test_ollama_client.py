import pytest
import app.client as oc


@pytest.fixture(autouse=True)
def reset():
    oc.clear_history()
    yield
    oc.clear_history()


def test_append_and_get():
    oc.append_to_history("user", "hello")
    oc.append_to_history("assistant", "hi")
    h = oc.get_history()
    assert h == [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi"},
    ]


def test_history_capped():
    for i in range(oc.MAX_HISTORY + 5):
        oc.append_to_history("user", f"msg {i}")
    assert len(oc.get_history()) == oc.MAX_HISTORY


def test_oldest_dropped_first():
    for i in range(oc.MAX_HISTORY + 2):
        oc.append_to_history("user", f"msg {i}")
    assert oc.get_history()[0]["content"] == "msg 2"


def test_clear():
    oc.append_to_history("user", "x")
    oc.clear_history()
    assert oc.get_history() == []


def test_remove_last():
    oc.append_to_history("user", "first")
    oc.append_to_history("user", "second")
    oc.remove_last_message()
    assert len(oc.get_history()) == 1
    assert oc.get_history()[0]["content"] == "first"


def test_remove_last_empty_is_safe():
    oc.remove_last_message()  # must not raise
    assert oc.get_history() == []


def test_build_messages_has_system_prompt():
    oc.append_to_history("user", "what is python?")
    msgs = oc.build_messages()
    assert msgs[0]["role"] == "system"
    assert "coding assistant" in msgs[0]["content"].lower()
    assert msgs[1] == {"role": "user", "content": "what is python?"}


def test_build_messages_empty_history():
    msgs = oc.build_messages()
    assert len(msgs) == 1
    assert msgs[0]["role"] == "system"
