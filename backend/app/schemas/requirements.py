"""Typed conversation state and the much smaller model-controlled patch."""

from typing import Literal
from pydantic import BaseModel, ConfigDict, Field
from pydantic.json_schema import GetJsonSchemaHandler
from pydantic_core import CoreSchema
import pydantic_core

UseCase = Literal["general", "programming", "gaming", "creative", "machine_learning"]
Preference = Literal["lightweight", "battery", "performance", "value"]
MlMode = Literal["local", "cloud", "both", "unsure"]
FieldName = Literal[
    "category",
    "use_cases",
    "budget_max_inr",
    "no_budget",
    "min_ram_gb",
    "min_storage_gb",
    "require_dedicated_gpu",
    "max_weight_kg",
    "min_battery_hours",
    "required_features",
    "preferences",
    "ml_mode",
]


class Requirements(BaseModel):
    model_config = ConfigDict(extra="forbid")
    category: str = "laptop"
    use_cases: list[UseCase] = Field(default_factory=list, max_length=5)
    budget_max_inr: int | None = Field(default=None, gt=0, le=10000000)
    no_budget: bool = False
    min_ram_gb: int | None = Field(default=None, gt=0, le=1024)
    min_storage_gb: int | None = Field(default=None, gt=0, le=100000)
    require_dedicated_gpu: bool | None = None
    max_weight_kg: float | None = Field(default=None, gt=0, le=20)
    min_battery_hours: float | None = Field(default=None, gt=0, le=72)
    required_features: list[str] = Field(default_factory=list, max_length=12)
    preferences: list[Preference] = Field(default_factory=list, max_length=4)
    ml_mode: MlMode | None = None
    conflicts: list[str] = Field(default_factory=list)
    provenance: dict[str, str] = Field(default_factory=dict)
    pending_budget: int | None = None

    # Application-managed dialogue state and provisional assumptions
    pending_clarification: str | None = None
    clarification_field: str | None = None
    clarification_attempts: dict[str, int] = Field(default_factory=dict)
    provisional_assumptions: dict[str, str] = Field(default_factory=dict)
    rejected_budget_proposals: list[int] = Field(default_factory=list)


class _AnyJsonValue:
    """Custom type that generates a JSON Schema accepted by Groq strict mode.

    Groq strict mode does not allow anyOf[integer, number] (overlap).
    We use anyOf[string, number, boolean, array, null] where 'number'
    covers both integers and floats (Groq accepts this).
    Pydantic validates received values permissively.
    """

    @classmethod
    def __get_validators__(cls):
        yield lambda v: v

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler) -> CoreSchema:
        return pydantic_core.core_schema.any_schema()

    @classmethod
    def __get_pydantic_json_schema__(cls, schema: CoreSchema, handler: GetJsonSchemaHandler):
        # Groq accepts: string | number | boolean | array | null
        # 'number' covers both integer and float without overlap ambiguity.
        return {
            "anyOf": [
                {"type": "string"},
                {"type": "number"},
                {"type": "boolean"},
                {"type": "array", "items": {"type": "string"}},
                {"type": "null"},
            ]
        }


class Change(BaseModel):
    model_config = ConfigDict(extra="forbid")
    field: FieldName
    action: Literal["set", "clear"]
    # Accepts any JSON value. The JSON Schema emitted to Groq uses a
    # non-overlapping anyOf that Groq strict mode accepts. The state merger
    # in state.py enforces the correct per-field type after receiving it.
    value_json: _AnyJsonValue | None
    evidence: str


class Extraction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    intent: Literal["recommend", "details", "compare", "greeting", "out_of_scope"]
    changes: list[Change]
    conflicts: list[str]
    proposal_decision: Literal["accept", "reject", "none"]
    product_ids: list[str]
