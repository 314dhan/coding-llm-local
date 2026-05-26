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
    with patch("app.client") as mock_client:
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Use a for loop.")]
        mock_client.messages.create.return_value = mock_response

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
    with patch("app.client") as mock_client:
        mock_resp1 = MagicMock()
        mock_resp1.content = [MagicMock(text="Answer 1")]
        mock_resp2 = MagicMock()
        mock_resp2.content = [MagicMock(text="Answer 2")]
        mock_client.messages.create.side_effect = [mock_resp1, mock_resp2]

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

        second_call_args = mock_client.messages.create.call_args
        messages = second_call_args.kwargs["messages"]
        assert len(messages) == 3
        assert messages[0] == {"role": "user", "content": "First question"}
        assert messages[1] == {"role": "assistant", "content": "Answer 1"}
        assert messages[2] == {"role": "user", "content": "Second question"}
