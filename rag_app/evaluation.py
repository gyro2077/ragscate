from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from rag_app.config import Settings
from rag_app.generation.citations import CitationValidator
from rag_app.generation.providers import DisabledProvider
from rag_app.generation.service import AnswerService
from rag_app.retrieval.hybrid import HybridRetriever
from rag_app.retrieval.semantic import SemanticEncoder
from rag_app.storage.database import connect, latest_snapshot_id


@dataclass(frozen=True)
class EvaluationResult:
    total: int
    passed: int
    top3_passed: int
    citation_count: int
    valid_citations: int
    abstention_passed: bool
    rows: list[dict[str, object]]

    @property
    def success(self) -> bool:
        return self.total == self.passed and self.citation_count == self.valid_citations and self.abstention_passed


def load_gold(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def evaluate(settings: Settings, encoder: SemanticEncoder, gold_path: Path | None = None) -> EvaluationResult:
    gold_path = gold_path or settings.root / "evals" / "golden_questions.jsonl"
    cases = load_gold(gold_path)
    connection = connect(settings.database_path)
    try:
        snapshot = latest_snapshot_id(connection)
        if not snapshot:
            raise RuntimeError("No existe snapshot para evaluar")
        retriever = HybridRetriever(connection, settings.data_dir, encoder)
        validator = CitationValidator(settings.root, connection)
        service = AnswerService(connection, retriever, validator, DisabledProvider())
        rows: list[dict[str, object]] = []
        citation_count = valid_citations = top3_passed = passed = 0
        abstention_passed = False
        for case in cases:
            answer = service.ask(snapshot, str(case["question"]))
            expected_list = list(case.get("expected_members", []))
            expected = set(expected_list)
            hits = retriever.search(snapshot, str(case["question"]), top_k=3) if expected else []
            top_members = {h.chunk.member_name for h in hits} | {h.chunk.object_name for h in hits}
            # Todos los simbolos esperados de localizacion deben quedar en top 3.
            top3 = not expected or expected.issubset(top_members)
            if top3 and expected:
                top3_passed += 1
            citations_ok = all(validator.validate(c) for c in answer.citations)
            citation_count += len(answer.citations)
            valid_citations += sum(validator.validate(c) for c in answer.citations)
            text_ok = not case.get("must_contain") or str(case["must_contain"]).lower() in answer.answer.lower()
            classification_ok = answer.classification == case["classification"]
            members_cited = {c.member for c in answer.citations}
            evidence_ok = not expected or expected.issubset(members_cited)
            case_pass = classification_ok and citations_ok and text_ok and evidence_ok and top3
            if case["classification"] == "No localizado":
                abstention_passed = classification_ok and not answer.citations
                case_pass = case_pass and abstention_passed
            passed += int(case_pass)
            rows.append({
                "id": case["id"], "classification": answer.classification, "top3": top3,
                "citations_valid": citations_ok, "evidence_complete": evidence_ok, "passed": case_pass,
            })
        return EvaluationResult(len(cases), passed, top3_passed, citation_count, valid_citations, abstention_passed, rows)
    finally:
        connection.close()


def write_report(path: Path, result: EvaluationResult, snapshot_id: str, encoder: SemanticEncoder) -> None:
    lines = [
        "# Evaluación reproducible de RAGscate", "",
        f"- Fecha UTC: `{datetime.now(timezone.utc).isoformat()}`",
        f"- Snapshot: `{snapshot_id}`", f"- Embeddings: `{encoder.provider_name}` / `{encoder.model_name}`",
        f"- Casos aprobados: **{result.passed}/{result.total}**",
        f"- Localizaciones top 3: **{result.top3_passed}/{result.total - 1}**",
        f"- Citas válidas: **{result.valid_citations}/{result.citation_count}**",
        f"- Abstención correcta: **{'sí' if result.abstention_passed else 'no'}**", "",
        "| Caso | Clasificación | Top 3 | Citas | Evidencia | Resultado |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in result.rows:
        mark = lambda value: "sí" if value else "no"
        lines.append(f"| {row['id']} | {row['classification']} | {mark(row['top3'])} | {mark(row['citations_valid'])} | {mark(row['evidence_complete'])} | {mark(row['passed'])} |")
    lines.extend(["", "El evaluador usa el proveedor LLM deshabilitado: mide ingesta, recuperación, composición determinista, abstención y reconstrucción exacta de citas.", ""])
    path.write_text("\n".join(lines), encoding="utf-8")
