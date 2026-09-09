from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from rag_app.config import get_settings
from rag_app.evaluation import evaluate, write_report
from rag_app.generation.citations import CitationValidator
from rag_app.generation.providers import create_llm_provider
from rag_app.generation.service import AnswerService
from rag_app.indexer import create_encoder, index_corpus
from rag_app.llm_evaluation import benchmark_llm, write_llm_report
from rag_app.retrieval.hybrid import HybridRetriever
from rag_app.storage.database import connect, latest_snapshot_id


def _json(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def _stack(settings):
    encoder = create_encoder(settings)
    connection = connect(settings.database_path)
    snapshot = latest_snapshot_id(connection)
    if not snapshot:
        connection.close()
        raise SystemExit("No existe un índice. Ejecute: ragscate index")
    return encoder, connection, snapshot, HybridRetriever(connection, settings.data_dir, encoder)


def main() -> None:
    parser = argparse.ArgumentParser(prog="ragscate", description="RAG local verificable para PowerBuilder")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("index", help="Ingiere el corpus y crea un snapshot")
    search = commands.add_parser("search", help="Ejecuta recuperación híbrida")
    search.add_argument("query"); search.add_argument("--top-k", type=int, default=8)
    ask = commands.add_parser("ask", help="Responde con evidencia validada")
    ask.add_argument("question")
    evaluation = commands.add_parser("evaluate", help="Ejecuta las preguntas doradas")
    evaluation.add_argument("--report", default="EVALUACION-RAG.md")
    health = commands.add_parser("llm-health", help="Comprueba endpoint y modelo LLM sin generar")
    benchmark = commands.add_parser("benchmark-llm", help="Evalúa un modelo Ollama instalado sin descargarlo")
    benchmark.add_argument("--model", help="Modelo Ollama; por defecto usa RAG_LLM_MODEL")
    benchmark.add_argument("--repetitions", type=int, default=3)
    benchmark.add_argument("--cases", default="evals/llm_questions.jsonl")
    benchmark.add_argument("--case-id", action="append", default=[], help="Ejecuta solo un ID; puede repetirse")
    benchmark.add_argument("--report", default="EVALUACION-LLM-LOCAL.md")
    serve = commands.add_parser("serve", help="Inicia API e interfaz")
    serve.add_argument("--host", default="127.0.0.1"); serve.add_argument("--port", default=8000, type=int)
    args = parser.parse_args()
    settings = get_settings()

    if args.command == "index":
        _json(index_corpus(settings))
        return
    if args.command == "serve":
        import uvicorn
        uvicorn.run("rag_app.api.main:app", host=args.host, port=args.port, reload=False)
        return
    if args.command == "llm-health":
        _json(create_llm_provider(settings).health().to_dict())
        return
    if args.command == "benchmark-llm":
        model = args.model or settings.llm_model
        if not model:
            raise SystemExit("Indique --model o configure RAG_LLM_MODEL")
        result = benchmark_llm(
            settings,
            model,
            args.repetitions,
            settings.root / args.cases,
            set(args.case_id) or None,
        )
        json_path = settings.data_dir / "llm-benchmarks" / f"{model.replace('/', '_').replace(':', '_')}.json"
        write_llm_report(settings.root / args.report, result, json_path)
        _json({
            "success": result.success,
            "model": result.model,
            "passed": result.passed_runs,
            "total": result.total_runs,
            "report": args.report,
            "json_report": str(json_path.relative_to(settings.root)),
        })
        if not result.success:
            raise SystemExit(1)
        return
    encoder, connection, snapshot, retriever = _stack(settings)
    try:
        if args.command == "search":
            hits = retriever.search(snapshot, args.query, args.top_k)
            _json([{**h.chunk.to_dict(), "score": h.score, "lexical_rank": h.lexical_rank, "semantic_rank": h.semantic_rank, "exact_symbol": h.exact_symbol, "expanded": h.expanded} for h in hits])
        elif args.command == "ask":
            service = AnswerService(
                connection, retriever, CitationValidator(settings.root, connection),
                create_llm_provider(settings), settings.max_context_chars, settings.llm_json_retries,
            )
            _json(asdict(service.ask(snapshot, args.question)))
        elif args.command == "evaluate":
            result = evaluate(settings, encoder)
            write_report(settings.root / args.report, result, snapshot, encoder)
            _json({"success": result.success, "passed": result.passed, "total": result.total, "report": args.report})
            if not result.success:
                raise SystemExit(1)
    finally:
        connection.close()


if __name__ == "__main__":
    main()
