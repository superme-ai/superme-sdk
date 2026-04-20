"""Tests for InterviewsMixin — unit (mocked) + live e2e.

Unit tests run on every commit with no external dependencies.
Live tests require SUPERME_API_KEY and run with ``pytest -m live``.
"""

from __future__ import annotations

import os

import httpx
import pytest
import respx

from superme_sdk.client import SuperMeClient

REST_BASE = "https://www.superme.ai"

# ---------------------------------------------------------------------------
# Fake JWT with user_id "uid_123"
# Middle segment is base64url of {"user_id":"uid_123"}
# ---------------------------------------------------------------------------
FAKE_JWT = "eyJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoidWlkXzEyMyJ9.sig"


# ---------------------------------------------------------------------------
# Part A — Unit tests (mocked, always run)
# ---------------------------------------------------------------------------


class TestContractAllMethodsExist:
    def test_all_methods_present(self):
        expected = [
            "start_interview",
            "get_interview_status",
            "get_interview_transcript",
            "list_my_interviews",
            "stream_interview",
        ]
        for name in expected:
            assert hasattr(SuperMeClient, name), f"SuperMeClient missing method: {name}"
            assert callable(getattr(SuperMeClient, name))


class TestStartInterview:
    @respx.mock
    def test_start_interview_posts_correct_body(self):
        route = respx.post(f"{REST_BASE}/api/v3/interview/start-agent").mock(
            return_value=httpx.Response(
                200, json={"interview_id": "iv_1", "status": "preparing"}
            )
        )
        client = SuperMeClient(api_key=FAKE_JWT)
        client.start_interview(role_id="role_abc")

        body = route.calls[0].request.read()
        import json

        parsed = json.loads(body)
        assert parsed == {"role_id": "role_abc"}
        client.close()

    @respx.mock
    def test_start_interview_returns_response(self):
        respx.post(f"{REST_BASE}/api/v3/interview/start-agent").mock(
            return_value=httpx.Response(
                200, json={"interview_id": "iv_1", "status": "preparing"}
            )
        )
        client = SuperMeClient(api_key=FAKE_JWT)
        result = client.start_interview(role_id="role_abc")
        assert result == {"interview_id": "iv_1", "status": "preparing"}
        client.close()

    @respx.mock
    def test_start_interview_4xx_raises(self):
        respx.post(f"{REST_BASE}/api/v3/interview/start-agent").mock(
            return_value=httpx.Response(422, json={"error": "invalid role"})
        )
        client = SuperMeClient(api_key=FAKE_JWT)
        with pytest.raises(RuntimeError):
            client.start_interview(role_id="bad_role")
        client.close()


class TestGetInterviewStatus:
    @respx.mock
    def test_get_interview_status_calls_correct_url(self):
        route = respx.get(f"{REST_BASE}/api/v3/interview/iv_1/status").mock(
            return_value=httpx.Response(
                200, json={"interview_id": "iv_1", "status": "active"}
            )
        )
        client = SuperMeClient(api_key=FAKE_JWT)
        result = client.get_interview_status("iv_1")
        assert route.called
        assert result == {"interview_id": "iv_1", "status": "active"}
        client.close()


class TestGetInterviewTranscript:
    @respx.mock
    def test_get_interview_transcript_calls_correct_url(self):
        route = respx.get(f"{REST_BASE}/api/v3/interview/iv_1/transcript").mock(
            return_value=httpx.Response(
                200, json={"transcript": [{"stage": "intro", "messages": []}]}
            )
        )
        client = SuperMeClient(api_key=FAKE_JWT)
        result = client.get_interview_transcript("iv_1")
        assert route.called
        assert result == {"transcript": [{"stage": "intro", "messages": []}]}
        client.close()


class TestListMyInterviews:
    @respx.mock
    def test_list_my_interviews_calls_user_endpoint(self):
        route = respx.get(f"{REST_BASE}/api/v3/interview/by-user/uid_123").mock(
            return_value=httpx.Response(
                200,
                json={
                    "interviews": [
                        {"interview_id": "iv_1", "status": "completed"},
                        {"interview_id": "iv_2", "status": "active"},
                    ]
                },
            )
        )
        client = SuperMeClient(api_key=FAKE_JWT)
        result = client.list_my_interviews()
        assert route.called
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["interview_id"] == "iv_1"
        client.close()

    def test_list_my_interviews_raises_if_no_user_id(self):
        # JWT with no user_id in payload: header.{}.sig
        import base64
        import json as _json

        empty_payload = (
            base64.urlsafe_b64encode(_json.dumps({}).encode()).rstrip(b"=").decode()
        )
        no_uid_jwt = f"eyJhbGciOiJIUzI1NiJ9.{empty_payload}.sig"
        client = SuperMeClient(api_key=no_uid_jwt)
        with pytest.raises(ValueError, match="user_id"):
            client.list_my_interviews()
        client.close()


class TestStreamInterview:
    @pytest.mark.parametrize("status", ["completed", "scoring", "scored", "failed", "withdrawn"])
    @respx.mock
    def test_stream_terminal_status_stops_after_one_event(self, status):
        content = f'data: {{"event": "status", "status": "{status}"}}\n\n'.encode()
        respx.get(f"{REST_BASE}/api/v3/interview/iv_1/stream").mock(
            return_value=httpx.Response(
                200,
                content=content,
                headers={"content-type": "text/event-stream"},
            )
        )
        client = SuperMeClient(api_key=FAKE_JWT)
        events = list(client.stream_interview("iv_1"))
        assert len(events) == 1
        assert events[0]["status"] == status
        client.close()

    @respx.mock
    def test_stream_non_terminal_status_yields_multiple_events(self):
        content = (
            b'data: {"event": "status", "status": "active"}\n\n'
            b'data: {"event": "status", "status": "completed"}\n\n'
        )
        respx.get(f"{REST_BASE}/api/v3/interview/iv_1/stream").mock(
            return_value=httpx.Response(
                200,
                content=content,
                headers={"content-type": "text/event-stream"},
            )
        )
        client = SuperMeClient(api_key=FAKE_JWT)
        events = list(client.stream_interview("iv_1"))
        assert len(events) == 2
        assert events[0]["status"] == "active"
        assert events[1]["status"] == "completed"
        client.close()

    def test_terminal_set_is_exact(self):
        """The terminal status set must match exactly what the implementation uses."""
        import inspect
        import re

        from superme_sdk.services._interviews import InterviewsMixin

        source = inspect.getsource(InterviewsMixin.stream_interview)
        match = re.search(r"terminal\s*=\s*\{([^}]+)\}", source)
        assert match, "Could not find terminal set in stream_interview source"
        raw = match.group(1)
        found = {s.strip().strip('"').strip("'") for s in raw.split(",")}
        assert found == {"completed", "scoring", "scored", "failed", "withdrawn"}


# ---------------------------------------------------------------------------
# Part B — Live e2e tests (require SUPERME_API_KEY, run with -m live)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def live_rest_client():
    key = os.getenv("SUPERME_API_KEY", "")
    if not key:
        pytest.skip("SUPERME_API_KEY not set")
    from superme_sdk.client import SuperMeClient as _SMC

    client = _SMC(api_key=key)
    yield client
    client.close()


@pytest.mark.live
def test_live_roles_and_start_interview(live_rest_client):
    """Exercises start_interview, get_interview_status, get_interview_transcript."""
    roles = live_rest_client.list_active_roles(limit=3)
    assert isinstance(roles, list), "list_active_roles should return a list"
    assert len(roles) >= 1, "Need at least one active role to run this test"

    role = roles[0]
    resp = live_rest_client.start_interview(role_id=role["id"])
    assert "interview_id" in resp, (
        f"start_interview response missing interview_id: {resp}"
    )
    interview_id = resp["interview_id"]

    status_resp = live_rest_client.get_interview_status(interview_id)
    assert isinstance(status_resp, dict)

    transcript_resp = live_rest_client.get_interview_transcript(interview_id)
    assert isinstance(transcript_resp, dict)


@pytest.mark.live
def test_live_list_my_interviews(live_rest_client):
    """list_my_interviews returns a list; non-empty items have expected keys."""
    interviews = live_rest_client.list_my_interviews()
    assert isinstance(interviews, list)
    if interviews:
        first = interviews[0]
        assert "interview_id" in first, f"item missing interview_id: {first}"
        assert "status" in first, f"item missing status: {first}"


@pytest.mark.live
def test_live_list_companies_and_roles(live_rest_client):
    """list_active_roles returns role dicts with id and title."""
    roles = live_rest_client.list_active_roles(limit=5)
    assert isinstance(roles, list)
    for role in roles:
        assert "id" in role, f"role missing id: {role}"
        assert "title" in role, f"role missing title: {role}"
