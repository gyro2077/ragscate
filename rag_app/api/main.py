from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from rag_app.config import Settings, get_settings
from rag_app.generation.citations import CitationValidationError, CitationValidator
from rag_app.generation.providers import create_llm_provider
from rag_app.generation.service import AnswerService
from rag_app.indexer import create_encoder, index_corpus
from rag_app.retrieval.hybrid import HybridRetriever
from rag_app.retrieval.semantic import SemanticEncoder
from rag_app.storage.database import connect, latest_snapshot_id, list_snapshots

from .schemas import AskRequest, AskResponse, SearchHitResponse, SearchRequest


WEB_ROOT = Path(__file__).resolve().parents[1] / "web"


def create_app(settings: Settings | None = None, encoder: SemanticEncoder | None = None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(title="RAGscate", version="0.1.0")
    app.state.settings = settings
    app.state.encoder = encoder
    templates = Jinja2Templates(directory=str(WEB_ROOT / "templates"))
    app.mount("/static", StaticFiles(directory=str(WEB_ROOT / "static")), name="static")

    def stack():
        connection = connect(settings.database_path)
        snapshot = latest_snapshot_id(connection)
        if snapshot is None:
            connection.close()
            raise HTTPException(409, "No existe un snapshot. Ejecute ragscate index.")
        if app.state.encoder is None:
            app.state.encoder = create_encoder(settings)
        active_encoder = app.state.encoder
        retriever = HybridRetriever(connection, settings.data_dir, active_encoder)
        return connection, snapshot, retriever

    @app.get("/", response_class=HTMLResponse)
    def home(request: Request):
        return templates.TemplateResponse(request=request, name="index.html", context={"title": "RAGscate"})

    @app.get("/api/health")
    def health():
        connection = connect(settings.database_path)
        try:
            snapshot = latest_snapshot_id(connection)
        finally:
            connection.close()
        return {"status": "ok", "indexed": snapshot is not None, "snapshot_id": snapshot, "llm_provider": settings.llm_provider}

    @app.get("/api/snapshots")
    def snapshots():
        connection = connect(settings.database_path)
        try:
            return list_snapshots(connection)
        finally:
            connection.close()

    @app.post("/api/index")
    def index():
        return index_corpus(settings, app.state.encoder)

    @app.post("/api/search", response_model=list[SearchHitResponse])
    def search(payload: SearchRequest):
        connection, latest, retriever = stack()
        try:
            snapshot_id = payload.snapshot_id or latest
            hits = retriever.search(snapshot_id, payload.query, payload.top_k, payload.object_type, payload.member_type, payload.pbl)
            return [SearchHitResponse(
                chunk_id=h.chunk.chunk_id, score=h.score, pbl=h.chunk.pbl, file=h.chunk.source_path,
                object=h.chunk.object_name, object_type=h.chunk.object_type, member=h.chunk.member_name,
                member_type=h.chunk.member_type, control=h.chunk.control_name,
                start_line=h.chunk.start_line, end_line=h.chunk.end_line,
                exact_symbol=h.exact_symbol, expanded=h.expanded,
            ) for h in hits]
        finally:
            connection.close()

    @app.post("/api/ask", response_model=AskResponse)
    def ask(payload: AskRequest):
        connection, latest, retriever = stack()
        try:
            snapshot_id = payload.snapshot_id or latest
            service = AnswerService(
                connection, retriever, CitationValidator(settings.root, connection),
                create_llm_provider(settings), settings.max_context_chars,
            )
            return AskResponse.model_validate(asdict(service.ask(snapshot_id, payload.question)))
        except CitationValidationError as exc:
            raise HTTPException(409, str(exc)) from exc
        finally:
            connection.close()

    @app.get("/api/source/{chunk_id}")
    def source(chunk_id: str, start_line: int | None = None, end_line: int | None = None):
        connection = connect(settings.database_path)
        try:
            row = connection.execute("SELECT * FROM chunks WHERE chunk_id=?", (chunk_id,)).fetchone()
            if row is None:
                raise HTTPException(404, "Fragmento no encontrado")
            from rag_app.storage.database import chunk_from_row
            return asdict(CitationValidator(settings.root, connection).build(chunk_from_row(row), start_line, end_line))
        except CitationValidationError as exc:
            raise HTTPException(409, str(exc)) from exc
        finally:
            connection.close()

    return app


app = create_app()
