import json
import pytest
from unittest.mock import MagicMock, patch
from app import app as flask_app


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    flask_app.config["SECRET_KEY"] = "test-secret-key"
    with flask_app.test_client() as client:
        yield client


def test_index_returns_200(client):
    response = client.get("/")
    assert response.status_code == 200


def test_index_contains_chat_ui(client):
    response = client.get("/")
    assert b"Coding Support Agent" in response.data


def test_chat_empty_message_returns_400(client):
    with client.session_transaction() as sess:
        sess["session_id"] = "test-session-empty"
    response = client.post(
        "/chat",
        data=json.dumps({"message": ""}),
        content_type="application/json",
    )
    assert response.status_code == 400


def test_chat_missing_message_returns_400(client):
    with client.session_transaction() as sess:
        sess["session_id"] = "test-session-missing"
    response = client.post(
        "/chat",
        data=json.dumps({}),
        content_type="application/json",
    )
    assert response.status_code == 400


def test_chat_returns_reply(client):
    mock_response = MagicMock()
    mock_response.message.content = "Use a for loop."

    with patch("app.ollama.chat", return_value=mock_response):
        with client.session_transaction() as sess:
            sess["session_id"] = "test-session-reply"

        response = client.post(
            "/chat",
            data=json.dumps({"message": "How do I loop in Python?"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["reply"] == "Use a for loop."


def test_chat_history_accumulates(client):
    mock_resp1 = MagicMock()
    mock_resp1.message.content = "Answer 1"
    mock_resp2 = MagicMock()
    mock_resp2.message.content = "Answer 2"

    with patch("app.ollama.chat", side_effect=[mock_resp1, mock_resp2]) as mock_chat:
        with client.session_transaction() as sess:
            sess["session_id"] = "test-session-history"

        client.post(
            "/chat",
            data=json.dumps({"message": "First question"}),
            content_type="application/json",
        )
        client.post(
            "/chat",
            data=json.dumps({"message": "Second question"}),
            content_type="application/json",
        )

        second_call_args = mock_chat.call_args
        messages = second_call_args.kwargs["messages"]
        # messages includes system prompt + history: system, user1, assistant1, user2
        user_messages = [m for m in messages if m["role"] != "system"]
        assert len(user_messages) == 3
        assert user_messages[0] == {"role": "user", "content": "First question"}
        assert user_messages[1] == {"role": "assistant", "content": "Answer 1"}
        assert user_messages[2] == {"role": "user", "content": "Second question"}
