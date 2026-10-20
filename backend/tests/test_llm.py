import json
import httpx
import pytest
from app.agent.llm_client import GroqExtractor
from app.schemas.requirements import Requirements
from app.config import Settings
from app.errors import AppError


def adapter(handler):
    return GroqExtractor(Settings(_env_file=None, groq_api_key="test-only-key"), httpx.MockTransport(handler))


def call(a):
    return a.extract("Programming under 80000", Requirements(), [], [])


@pytest.mark.parametrize(
    "status,code",
    [
        (401, "llm_auth"),
        (403, "llm_auth"),
        (429, "llm_rate_limit"),
        (500, "llm_unavailable"),
        (400, "llm_request_rejected"),
    ],
)
def test_provider_errors(status, code):
    with pytest.raises(AppError) as exc:
        call(adapter(lambda req: httpx.Response(status, json={})))
    assert exc.value.code == code


def test_missing_key():
    with pytest.raises(AppError) as exc:
        call(GroqExtractor(Settings(_env_file=None, groq_api_key="")))
    assert exc.value.code == "llm_not_configured"


def test_timeout():
    def handler(request):
        raise httpx.ReadTimeout("test")

    with pytest.raises(AppError) as exc:
        call(adapter(handler))
    assert exc.value.status == 504


def test_malformed_output_has_one_repair():
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(
            200, json={"choices": [{"finish_reason": "stop", "message": {"content": "not json"}}]}
        )

    with pytest.raises(AppError):
        call(adapter(handler))
    assert len(calls) == 2


def test_success_payload():
    def handler(request):
        body = json.loads(request.content)
        assert body["response_format"]["json_schema"]["strict"] is True
        content = json.dumps(
            {
                "intent": "recommend",
                "changes": [],
                "conflicts": [],
                "proposal_decision": "none",
                "product_ids": [],
            }
        )
        return httpx.Response(
            200, json={"choices": [{"finish_reason": "stop", "message": {"content": content}}]}
        )

    assert call(adapter(handler)).intent == "recommend"
