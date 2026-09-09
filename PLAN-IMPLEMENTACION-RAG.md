# Plan de implementacion de RAGscate

## Resultado buscado

Construir un asistente local de lectura de codigo PowerBuilder que responda en
espanol usando exclusivamente evidencia recuperada de `pb-src/`. Cada respuesta
debe identificar la PBL, archivo, objeto, miembro y lineas exactas, y marcarse
como `Comprobado`, `Inferido` o `No localizado`.

El asistente explica codigo y propone lugares de revision. No calcula primas
oficiales, no modifica fuentes PowerBuilder y no reemplaza la compilacion o las
pruebas dentro de PowerBuilder.

## Decisiones del MVP

- Ejecucion en Linux; PowerBuilder y WinBoat solo se necesitan para producir o
  volver a exportar fuentes `SR*`.
- Python 3.11 o superior.
- FastAPI para la API y una interfaz web minima servida por la misma aplicacion.
- SQLite para manifiesto, metadatos, relaciones y busqueda lexical FTS5.
- Sentence Transformers para embeddings locales; el modelo se configura por
  variable de entorno y no se codifica dentro de la logica.
- Matriz de embeddings local y versionada por `snapshot_id`; no se necesita un
  servidor vectorial para el corpus inicial.
- Proveedor de LLM intercambiable mediante una interfaz. Las pruebas de parser,
  recuperacion y citas no deben depender de un LLM ni de Internet.
- Exportacion manual en la primera version. ORCA es una mejora posterior, siempre
  sobre una copia cerrada de las PBL.

Estas decisiones mantienen el piloto entendible. SQLite FTS5 proporciona
busqueda de texto y ranking BM25; Sentence Transformers cubre la recuperacion
semantica. La fusion de ambos resultados se implementa explicitamente para que
sea auditable.

## Arquitectura

### 1. Captura y version del corpus

Entrada: `pb-src/*.sr*`.

Generar `manifest.jsonl` sin alterar las fuentes. Cada registro debe contener:

- `snapshot_id`;
- commit Git, si existe;
- PBL de origen;
- ruta, nombre y tipo del objeto;
- extension PowerBuilder;
- tamano, fecha y SHA-256 del archivo;
- codificacion y terminadores de linea;
- fecha de indexacion.

El archivo `SR*` original es la autoridad. Cualquier texto normalizado para
embeddings se almacena por separado.

### 2. Parser PowerBuilder consciente de lineas

Implementar dos rutas de parsing:

- PowerScript: `.sra`, `.srw`, `.sru`, `.srs`, y posteriormente `.srm`, `.srf`.
- DataWindow: `.srd`, porque su sintaxis declarativa no sigue la misma estructura
  de funciones y eventos.

El parser PowerScript debe reconocer como minimo:

- cabecera `$PBExportHeader$` y comentarios de exportacion;
- tipo global, ancestro y clausula `within`;
- variables de instancia;
- prototypes;
- funciones y subrutinas, desde su declaracion hasta `end function` o
  `end subroutine`;
- eventos, desde `event nombre;` hasta `end event`;
- controles anidados;
- llamadas a funciones, eventos, objetos y DataWindows;
- Embedded SQL cuando aparezca en corpus futuro;
- continuaciones `&` y escapes PowerBuilder con `~`.

El parser DataWindow debe extraer:

- columnas, tipos, formatos y bandas;
- origen externo o sentencia de recuperacion;
- tablas, columnas, argumentos y procedimientos si existen;
- objetos visuales relevantes.

Para el corpus actual debe detectar que `d_tabla_primas_edad.srd` es externa y
no consulta ninguna tabla de base de datos.

### 3. Fragmentos, metadatos y relaciones

Crear fragmentos por unidad semantica, nunca por bloques arbitrarios de una
cantidad fija de caracteres:

- una funcion o subrutina;
- un evento;
- una seccion de variables;
- un control con su evento;
- la definicion de datos de una DataWindow;
- un fragmento de contexto del objeto para declaraciones e herencia.

Cada fragmento debe conservar:

```json
{
  "chunk_id": "sha256 estable",
  "snapshot_id": "commit o fecha-hash",
  "pbl": "cotizador_mvp.pbl",
  "source_path": "pb-src/n_cotizador_reglas.sru",
  "object_name": "n_cotizador_reglas",
  "object_type": "userobject",
  "member_type": "function",
  "member_name": "of_calcular_cotizacion",
  "control_name": null,
  "start_line": 60,
  "end_line": 133,
  "raw_sha256": "huella del texto exacto",
  "text": "fragmento exacto",
  "normalized_text": "copia solo para recuperacion"
}
```

Guardar relaciones en una tabla separada: `defines`, `contains`, `calls`,
`opens`, `uses_datawindow`, `inherits_from` y, cuando exista SQL, `reads_table`,
`writes_table` o `calls_procedure`.

### 4. Recuperacion hibrida

Flujo para cada pregunta:

1. Detectar nombres exactos como `of_calcular_cotizacion`, `cb_calcular` o
   `d_tabla_primas_edad` y aplicarles prioridad.
2. Buscar terminos y simbolos con SQLite FTS5/BM25.
3. Buscar significado con embeddings.
4. Fusionar rankings con Reciprocal Rank Fusion, sin mezclar directamente
   escalas incompatibles.
5. Aplicar filtros por snapshot, PBL, tipo de objeto y miembro.
6. Expandir como maximo un salto por relaciones pertinentes.
7. Entregar al generador pocos fragmentos completos, no lineas aisladas.

Para este corpus, una pregunta sobre el boton Calcular debe recuperar el evento
`cb_calcular.clicked`, luego `of_calcular` y finalmente
`n_cotizador_reglas.of_calcular_cotizacion`.

### 5. Generacion con citas verificables

Antes de llamar al LLM, el backend debe volver a abrir la fuente original,
extraer `start_line:end_line` y comprobar la huella del fragmento. Si no
coincide, se rechaza la cita y se exige reindexar.

Contrato de respuesta:

```json
{
  "classification": "Comprobado | Inferido | No localizado",
  "answer": "explicacion breve",
  "flow": ["paso 1", "paso 2"],
  "citations": [
    {
      "pbl": "cotizador_mvp.pbl",
      "file": "pb-src/w_cotizador_mvp.srw",
      "object": "w_cotizador_mvp",
      "member": "cb_calcular.clicked",
      "start_line": 576,
      "end_line": 580,
      "snippet": "texto exacto"
    }
  ],
  "possible_change_locations": [],
  "risks": [],
  "recommended_tests": []
}
```

Reglas:

- `Comprobado`: cada afirmacion sustancial aparece directamente en las citas.
- `Inferido`: la conclusion conecta varias evidencias y se identifica como tal.
- `No localizado`: no existe evidencia suficiente; no se rellena con conocimiento
  general del modelo.
- Una respuesta sin al menos una cita valida no puede ser `Comprobado`.
- El texto recuperado y los comentarios del codigo se tratan como datos, nunca
  como instrucciones para el modelo.

### 6. API e interfaz minima

API propuesta:

- `POST /api/index`: crea un nuevo snapshot del corpus.
- `GET /api/snapshots`: lista versiones indexadas.
- `POST /api/search`: devuelve fragmentos sin usar LLM.
- `POST /api/ask`: recupera, explica y cita.
- `GET /api/source/{chunk_id}`: devuelve el fragmento exacto y contexto.
- `GET /api/health`: comprueba aplicacion, indice y proveedor configurado.

Interfaz:

- caja de pregunta;
- selector de snapshot;
- respuesta y clasificacion;
- lista de citas con fragmentos expandibles;
- boton para abrir el archivo en la linea cuando el entorno lo permita;
- panel pequeno de flujo, riesgos y pruebas sugeridas.

No incluir autenticacion, edicion automatica, dashboard, administracion de
usuarios ni despliegue en nube en este MVP.

## Estructura propuesta

```text
rag_app/
├── api/
│   └── main.py
├── domain/
│   └── models.py
├── ingestion/
│   ├── discover.py
│   ├── manifest.py
│   ├── powerscript_parser.py
│   ├── datawindow_parser.py
│   └── chunker.py
├── retrieval/
│   ├── lexical.py
│   ├── semantic.py
│   ├── hybrid.py
│   └── relations.py
├── generation/
│   ├── citations.py
│   ├── prompts.py
│   └── providers.py
├── web/
│   ├── templates/index.html
│   └── static/
├── config.py
└── cli.py
rag-data/                 # generado; fuera de Git
evals/
├── golden_questions.jsonl
└── evaluate.py
tests/rag/
pyproject.toml
.env.example
```

## Fases y criterios de aceptacion

### Fase 0: linea base

- Preservar `pb-src/` y registrar su hash y commit.
- Crear configuracion, estructura y pruebas iniciales.
- Confirmar soporte FTS5 en el Python local.

Termina cuando el repositorio sigue limpio respecto de las fuentes PowerBuilder
y existe un comando de pruebas reproducible.

### Fase 1: ingesta y parser

- Generar manifiesto, chunks y relaciones.
- Probar limites exactos de funciones y eventos.
- Probar parser DataWindow externo.

Termina cuando cada chunk puede reconstruirse byte por byte desde su archivo y
rango de lineas.

### Fase 2: busqueda lexical y semantica

- Implementar FTS5, embeddings y fusion RRF.
- Añadir prioridad de simbolos y filtros.
- Exponer un CLI de busqueda sin LLM.

Termina cuando las preguntas conocidas recuperan la funcion o evento esperado
entre los primeros resultados.

### Fase 3: respuestas explicadas

- Implementar proveedor de LLM intercambiable.
- Validar todas las citas antes y despues de generar.
- Aplicar las tres clasificaciones.

Termina cuando no se puede producir una respuesta `Comprobado` sin evidencia
exacta y cuando una pregunta inexistente responde `No localizado`.

### Fase 4: interfaz local

- Implementar la pagina unica y los endpoints.
- Mostrar citas, lineas, version y fragmento.
- Permitir cambiar de snapshot.

Termina con una demostracion local completa desde pregunta hasta fragmento.

### Fase 5: evaluacion

- Crear preguntas doradas y resultados esperados.
- Medir recuperacion, exactitud de citas, clasificacion y abstencion.
- Guardar un reporte reproducible.

Umbrales del MVP:

- 100% de citas apuntan a lineas existentes y muestran texto exacto.
- 100% de preguntas doradas sobre simbolos recuperan el miembro esperado en top 3.
- 100% de preguntas sin evidencia se abstienen con `No localizado`.
- Los seis escenarios funcionales principales del cotizador se explican con
  evidencia, sin que el LLM invente formulas.

### Fase 6 opcional: exportacion con ORCA

Solo despues de estabilizar el parser:

- crear una utilidad Windows separada;
- trabajar sobre copias de PBL que no esten abiertas en el IDE;
- listar y exportar objetos con manifiesto;
- comparar hashes contra la exportacion manual;
- nunca importar o compilar automaticamente codigo de produccion.

## Preguntas doradas iniciales

1. ¿Donde se calcula la prima anual?
2. Explicame el flujo completo del boton Calcular.
3. ¿Que validaciones se aplican a la edad?
4. ¿Por que una persona de 70 anos con categoria Alto requiere autorizacion?
5. ¿Donde cambiaria el impuesto demostrativo?
6. ¿Que se veria afectado al agregar una categoria nueva?
7. ¿Que tabla de base de datos consulta `d_tabla_primas_edad`?
8. ¿Como se calcula la cuota mensual?
9. ¿Que hace el boton Limpiar?
10. ¿Donde se valida un supuesto campo `numero_poliza`?

La pregunta 7 debe explicar que la DataWindow es externa y se llena desde
PowerScript. La pregunta 10 debe responder `No localizado`.

## Referencias tecnicas

- Exportacion de objetos PowerBuilder: https://docs.appeon.com/pb2022/pbug/Exporting_and_importing_entries.html
- Funciones de gestion de bibliotecas ORCA: https://docs.appeon.com/pb2022/orca_guide/ch01s04s02.html
- SQLite FTS5: https://www.sqlite.org/fts5.html
- Sentence Transformers, busqueda semantica: https://www.sbert.net/examples/sentence_transformer/applications/semantic-search/README.html
- FastAPI, pruebas: https://fastapi.tiangolo.com/tutorial/testing/
