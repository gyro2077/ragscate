from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class GroundedLLMOutput(BaseModel):
    """Único contenido que se acepta de un LLM; nunca contiene citas completas."""

    model_config = ConfigDict(extra="forbid")

    evidence_sufficient: bool
    inferred: bool = False
    answer: str = Field(max_length=1800)
    evidence_ids: list[str] = Field(default_factory=list, max_length=8)
    flow: list[str] = Field(default_factory=list, max_length=8)
    possible_change_locations: list[str] = Field(default_factory=list, max_length=8)
    risks: list[str] = Field(default_factory=list, max_length=8)
    recommended_tests: list[str] = Field(default_factory=list, max_length=8)

    @field_validator(
        "answer",
        "flow",
        "possible_change_locations",
        "risks",
        "recommended_tests",
    )
    @classmethod
    def trim_text(cls, value):
        if isinstance(value, str):
            return value.strip()
        return [str(item).strip() for item in value if str(item).strip()]

    @field_validator("evidence_ids")
    @classmethod
    def unique_evidence_ids(cls, value: list[str]) -> list[str]:
        return list(dict.fromkeys(item.strip() for item in value if item.strip()))

    @model_validator(mode="after")
    def evidence_contract(self):
        if self.evidence_sufficient and (not self.answer or not self.evidence_ids):
            raise ValueError("Una respuesta suficiente requiere texto e IDs de evidencia")
        return self
