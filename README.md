# RAGscate

RAGscate es un asistente web local para comprender código PowerBuilder legado
mediante evidencia verificable. Ingiere fuentes exportadas `SR*`, conserva su
snapshot, combina búsqueda léxica y semántica y responde en español citando:

`PBL → archivo → objeto → control/evento/función → líneas → snapshot`

El corpus incluido es un cotizador completamente didáctico. Sus fórmulas no
corresponden a un producto real de seguros.

## Estado y alcance

El MVP incluye:

- manifiesto inmutable con SHA-256, commit Git y `snapshot_id`;
- parsers separados y conscientes de líneas para PowerScript y DataWindow;
- fragmentos semánticos de objetos, variables, rutinas, eventos, controles y
  secciones DataWindow;
- relaciones `contains`, `calls`, `opens`, `uses_datawindow`,
  `inherits_from` y referencias SQL cuando aparecen;
- SQLite FTS5/BM25, Sentence Transformers local y fusión RRF determinista;
- validación de cada cita contra la fuente original y su hash;
- proveedor LLM intercambiable (`disabled`, `ollama`, `openai-compatible`);
- CLI, API FastAPI, interfaz web y evaluación dorada reproducible.

No incluye autenticación, nube, edición de PowerBuilder, agentes de cambio,
ORCA, base vectorial externa ni Neo4j. El LLM solo explica fragmentos
recuperados; la localización, clasificación y validación de citas son del
backend determinista.

## Requisitos e instalación

- Linux y Python 3.12 (la versión está fijada en `.python-version`).
- `uv` para instalar exactamente el entorno de `uv.lock`.
- SQLite con FTS5, incluido en el Python usado por el proyecto.

```bash
cd /home/gyro/Documents/MVP-RAG-CODE
UV_CACHE_DIR=/tmp/ragscate-uv-cache uv sync --frozen
cp .env.example .env
set -a
source .env
set +a
```

`.env.example` no contiene secretos. `RAG_EMBED_MODEL` decide qué modelo
Sentence Transformers se descarga y utiliza. Cambiarlo exige volver a indexar.
El primer índice necesita acceso a la fuente configurada del modelo; las
consultas posteriores son locales.

## Uso rápido

```bash
UV_CACHE_DIR=/tmp/ragscate-uv-cache uv run ragscate index
uv run ragscate search "flujo del boton Calcular" --top-k 3
uv run ragscate ask "¿Donde se calcula la prima anual?"
uv run ragscate ask "¿Donde se valida numero_poliza?"
uv run ragscate evaluate
uv run ragscate serve --host 127.0.0.1 --port 8000
```

La evaluación genera `EVALUACION-RAG.md`. La interfaz queda disponible en
`http://127.0.0.1:8000` y muestra clasificación, respuesta, flujo, citas
expandibles, lugares de cambio, riesgos y pruebas.

## API

- `POST /api/index`: crea o reconstruye el snapshot del corpus actual.
- `GET /api/snapshots`: lista snapshots indexados.
- `POST /api/search`: búsqueda híbrida sin invocar un LLM.
- `POST /api/ask`: respuesta estructurada y citas ya validadas.
- `GET /api/source/{chunk_id}`: reconstruye el fragmento desde el original.
- `GET /api/health`: estado de la aplicación y del índice.

```bash
curl -s http://127.0.0.1:8000/api/ask \
  -H 'Content-Type: application/json' \
  -d '{"question":"¿Como se calcula la cuota mensual?"}'
```

`Comprobado` siempre contiene al menos una cita válida. `Inferido` separa la
conclusión de los fragmentos recuperados. `No localizado` se abstiene y no
incluye ubicaciones inventadas.

## Proveedores LLM

El valor predeterminado es `RAG_LLM_PROVIDER=disabled`. Así funcionan parser,
índice, recuperación, respuestas doradas y citas sin credenciales. Para usar
un modelo local se configuran variables de entorno:

```bash
RAG_LLM_PROVIDER=ollama
RAG_LLM_MODEL=<modelo disponible localmente>
RAG_LLM_BASE_URL=http://127.0.0.1:11434
```

También se admite `RAG_LLM_PROVIDER=openai-compatible`, con endpoint, modelo y,
si hace falta, `RAG_LLM_API_KEY`. Ningún modelo instalado, token ni endpoint
privado se codifica en la aplicación. El código y comentarios recuperados se
tratan como datos no confiables, nunca como instrucciones.

## Arquitectura y artefactos

```text
pb-src/                   fuente de autoridad, nunca modificada por RAGscate
rag_app/ingestion/        descubrimiento, manifiesto y parsers
rag_app/storage/          esquema SQLite, FTS5 y relaciones
rag_app/retrieval/        embeddings, BM25 y fusión RRF
rag_app/generation/       abstención, proveedores y citas verificadas
rag_app/api/              API FastAPI y contratos Pydantic
rag_app/web/              interfaz HTML/CSS/JS sin framework pesado
evals/                    diez preguntas doradas
tests/rag/                pruebas unitarias e integración
rag-data/                 snapshots, SQLite y matrices; ignorado por Git
```

Cada snapshot genera `manifest.jsonl`, `chunks.jsonl`, `relations.jsonl`,
`embeddings.npy`, `embedding_ids.json` y `embedding_meta.json`. Si una fuente
cambia después de indexar, la validación rechaza la cita y obliga a reindexar.
La DataWindow `d_tabla_primas_edad` está identificada como externa: no se
inventa ninguna tabla SQL.

## Pruebas

```bash
uv run pytest
uv run pytest --cov=rag_app --cov-report=term-missing
python3 tests/verificar_cotizador.py
```

La primera suite valida RAGscate. La última reproduce por separado las reglas
matemáticas del cotizador; no sustituye el Full Build ni la ejecución registrada
en [VALIDACION-PB9.md](VALIDACION-PB9.md).

## Documentación del piloto

- [PLAN-IMPLEMENTACION-RAG.md](PLAN-IMPLEMENTACION-RAG.md): contratos y fases.
- [MAPA-CODIGO-COTIZADOR.md](MAPA-CODIGO-COTIZADOR.md): mapa del corpus.
- [VALIDACION-PB9.md](VALIDACION-PB9.md): evidencia de PowerBuilder.
- [README-COTIZADOR-PB9.md](README-COTIZADOR-PB9.md): uso del cotizador.

## Limitaciones reales

- El parser cubre el subconjunto exportado necesario para el piloto; debe
  ampliarse al validarlo con construcciones de otros sistemas PowerBuilder.
- La expansión por grafo está limitada deliberadamente a un salto.
- El MVP detecta SQL con patrones conservadores; no reemplaza un parser SQL.
- En modo LLM deshabilitado, las preguntas doradas tienen respuestas
  deterministas y otras consultas relacionadas se clasifican como `Inferido`
  con sus fragmentos para revisión humana.

## Licencia

El código propio de RAGscate se publica bajo GNU AGPL v3. PowerBuilder y sus
componentes conservan sus licencias y no forman parte de esta distribución.
