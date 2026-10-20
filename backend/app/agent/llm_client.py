"""Small HTTP adapter. No provider SDK retries, paid fallback, or silent mock."""

import json
import httpx
from pydantic import ValidationError
from app.agent.prompts import SYSTEM_PROMPT
from app.errors import AppError
from app.schemas.requirements import Extraction


class GroqExtractor:
    mode = "live"

    def __init__(self, settings, transport=None):
        self.settings, self.transport = settings, transport

    def extract(self, message, state, recent, products):
        key = self.settings.groq_api_key.get_secret_value()
        if not key or key in ("CHANGE_ME", "<SET_LOCALLY>"):
            raise AppError(
                503, "llm_not_configured", "Set GROQ_API_KEY in backend/.env, then restart the backend."
            )
        context = {
            "state": state.model_dump(),
            "recent_messages": recent[-6:],
            "previous_products": products,
            "latest_user_message": message,
        }
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(context, ensure_ascii=False)},
        ]
        for attempt in range(2):
            body = {
                "model": self.settings.groq_model,
                "messages": messages,
                "max_completion_tokens": 2048,
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "requirement_patch",
                        "strict": True,
                        "schema": Extraction.model_json_schema(),
                    },
                },
            }
            try:
                with httpx.Client(
                    timeout=self.settings.llm_timeout_seconds, transport=self.transport
                ) as client:
                    response = client.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers={"Authorization": f"Bearer {key}"},
                        json=body,
                    )
            except httpx.TimeoutException:
                raise AppError(
                    504,
                    "llm_timeout",
                    "The language service timed out. Your previous state is unchanged; please retry.",
                    True,
                )
            except httpx.HTTPError:
                raise AppError(
                    503, "llm_unavailable", "The language service is unreachable. Please retry.", True
                )
            if response.status_code in (401, 403):
                raise AppError(
                    503,
                    "llm_auth",
                    "The configured Groq key or model access was rejected. Check backend configuration.",
                )
            if response.status_code == 429:
                raise AppError(
                    503,
                    "llm_rate_limit",
                    "The free API limit has been reached. Wait before retrying; no paid fallback was used.",
                    True,
                )
            if response.status_code >= 500:
                raise AppError(
                    503, "llm_unavailable", "The language service is temporarily unavailable.", True
                )
            if response.status_code != 200:
                raise AppError(
                    502,
                    "llm_request_rejected",
                    "The provider rejected the model/schema request. Check model availability and the configured schema.",
                )
            try:
                choice = response.json()["choices"][0]
                if choice.get("finish_reason") != "stop" or choice["message"].get("refusal"):
                    raise ValueError("Incomplete or refused extraction")
                return Extraction.model_validate_json(choice["message"]["content"])
            except (ValueError, KeyError, IndexError, TypeError, ValidationError):
                if attempt == 0:
                    messages.append(
                        {
                            "role": "user",
                            "content": "Previous output could not be validated. Return one complete object matching the schema. Do not add prose.",
                        }
                    )
        raise AppError(
            502,
            "invalid_extraction",
            "The language service returned an invalid interpretation. Please rephrase.",
            True,
        )
