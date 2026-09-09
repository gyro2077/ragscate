from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    snapshot_id: str | None = None


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    snapshot_id: str | None = None
    top_k: int = Field(default=8, ge=1, le=30)
    object_type: str | None = None
    member_type: str | None = None
    pbl: str | None = None


class CitationResponse(BaseModel):
    chunk_id: str
    pbl: str
    file: str
    object: str
    member: str
    start_line: int
    end_line: int
    snippet: str
    snapshot_id: str


class GenerationInfoResponse(BaseModel):
    provider: str
    model: str
    status: Literal["disabled", "not_invoked", "generated", "fallback", "rejected"]
    detail: str
    attempts: int
    total_duration_ms: float | None
    load_duration_ms: float | None
    prompt_tokens: int | None
    output_tokens: int | None
    tokens_per_second: float | None


class AskResponse(BaseModel):
    classification: Literal["Comprobado", "Inferido", "No localizado"]
    answer: str
    flow: list[str]
    citations: list[CitationResponse]
    possible_change_locations: list[str]
    risks: list[str]
    recommended_tests: list[str]
    generation: GenerationInfoResponse

    @model_validator(mode="after")
    def enforce_evidence_contract(self):
        if self.classification == "Comprobado" and not self.citations:
            raise ValueError("Comprobado requiere al menos una cita")
        if self.classification == "No localizado" and self.citations:
            raise ValueError("No localizado no puede incluir citas")
        return self


class SearchHitResponse(BaseModel):
    chunk_id: str
    score: float
    pbl: str
    file: str
    object: str
    object_type: str
    member: str
    member_type: str
    control: str | None
    start_line: int
    end_line: int
    exact_symbol: bool
    expanded: bool
