# Plan de implementación del LLM local de RAGscate

Fecha de análisis: 2026-09-08

## 1. Resultado buscado

RAGscate debe usar un LLM local únicamente para redactar explicaciones en
español a partir de fragmentos recuperados. El backend conserva el control de:

- la clasificación `Comprobado`, `Inferido` o `No localizado`;
- la selección y validación de citas;
- la ruta `PBL -> archivo -> objeto -> miembro -> líneas -> snapshot`;
- las fórmulas, relaciones y resultados deterministas;
- la abstención cuando no existe evidencia suficiente.

El modelo no podrá crear citas, cambiar rangos de líneas ni elevar una respuesta
a `Comprobado`. La frase provisional del modo sin LLM no deberá aparecer cuando
Ollama esté sano y el modelo configurado responda correctamente.

## 2. Línea base verificada en este equipo

Equipo observado:

- CPU: AMD Ryzen 9 7940HS, 8 núcleos y 16 hilos.
- GPU: NVIDIA GeForce RTX 4060 Laptop, 8 GiB de VRAM.
- RAM: 14 GiB utilizables de los 16 GiB instalados.
- Ollama: 0.33.3, escuchando solo en `127.0.0.1:11434`.

Prueba local con `qwen2.5:7b`, contexto de 4096 tokens y temperatura 0:

- modelo cargado `100% GPU` según `ollama ps`;
- VRAM observada: 4646 MiB;
- respuesta generada: 60 tokens en aproximadamente 1.21 s;
- velocidad aproximada: 49 tokens/s;
- primera petición: aproximadamente 18.8 s, de los cuales 17.4 s fueron carga
  en frío.

La respuesta resumió correctamente una fórmula suministrada como evidencia. Es
una prueba directa del modelo y de Ollama, no una validación end-to-end de la
aplicación RAGscate.

Al medir había presión de memoria: 2.9 GiB disponibles y casi toda la swap en
uso. Antes de una presentación se deben cerrar aplicaciones innecesarias,
esperar a que se libere memoria y volver a medir. No se deben terminar procesos
automáticamente desde RAGscate.

## 3. Modelos candidatos

### Candidato A: `qwen2.5:7b`

Es la línea base inmediata porque ya está instalado y se verificó 100% en GPU.
Permite desarrollar y demostrar la integración sin descargar nada.

### Candidato B: `qwen2.5-coder:7b`

Es el candidato principal para la evaluación comparativa por estar especializado
en código y tener un tamaño similar (aproximadamente 4.7 GB). Debe descargarse
solo con autorización expresa y no será elegido hasta ejecutar la misma batería
contra la línea base.

### Candidato C: `qwen3:4b`

Es el candidato de menor consumo (aproximadamente 2.5 GB) y puede reducir carga
en frío y presión de memoria. En la evaluación debe usarse con razonamiento
visible deshabilitado para obtener respuestas breves y estructuradas.

### Candidato D: `gemma3:4b`

Es una alternativa multilingüe ligera (aproximadamente 3.3 GB). Se probará solo
si los dos candidatos anteriores no ofrecen el equilibrio deseado.

No se recomienda como primera opción un modelo de 7.2-8.1 GB en una GPU de 8 GB:
deja poco margen para la caché de contexto y aumenta el riesgo de descargar
capas a CPU. Tampoco se usarán variantes etiquetadas como `uncensored` o
`aggressive` como base de una demostración orientada a respuestas estrictamente
fundamentadas.

## 4. Fases de implementación

### Fase 0: congelar la línea base

1. Ejecutar `pytest`, evaluación dorada y validación de citas con LLM
   deshabilitado.
2. Guardar resultados, commit, snapshot y hashes del corpus.
3. Confirmar que `pb-src/`, `.pbl`, `.pbt` y `.pbw` no cambian.
4. Registrar memoria, swap, VRAM y modelos instalados.

Criterio: la integración del LLM no puede degradar recuperación ni citas.

### Fase 1: configuración reproducible de Ollama

Extender `Settings` y `.env.example` con variables realmente consumidas por el
código:

```text
RAG_LLM_TIMEOUT_SECONDS=120
RAG_LLM_NUM_CTX=4096
RAG_LLM_MAX_TOKENS=500
RAG_LLM_TEMPERATURE=0
RAG_LLM_TOP_P=0.9
RAG_LLM_KEEP_ALIVE=10m
RAG_LLM_THINK=false
```

Agregar un health check del proveedor que compruebe endpoint y modelo. No debe
descargar modelos, iniciar Ollama ni cambiar la máquina.

Criterio: error explícito y útil si Ollama no está disponible o el modelo no
existe; ninguna caída silenciosa al texto genérico anterior.

### Fase 2: salida estructurada y fundamentada

1. Solicitar a Ollama JSON validado por un esquema estricto.
2. Entregar al modelo fragmentos numerados (`E1`, `E2`, etc.), nunca el corpus
   completo.
3. Separar instrucciones del sistema de código y comentarios recuperados.
4. Pedir los campos `answer`, `flow`, `possible_change_locations`, `risks`,
   `recommended_tests` y `evidence_ids`.
5. Ignorar cualquier ubicación textual que no corresponda a un fragmento
   permitido.
6. Construir citas únicamente en el backend a partir de `evidence_ids` y volver
   a validar archivo, líneas y hash.

Criterio: el modelo redacta; el backend decide clasificación y evidencia.

### Fase 3: abstención y manejo de fallos

Reglas:

- cero evidencia suficiente -> `No localizado`, sin invocar el modelo;
- evidencia directa y citas válidas -> `Comprobado`;
- conclusión razonable que no está expresada literalmente -> `Inferido`, con
  una frase que distinga evidencia y conclusión;
- JSON inválido, timeout o proveedor caído -> error de proveedor visible y
  recuperable, no una explicación aparentemente válida;
- un identificador ausente como `numero_poliza` -> `No localizado` sin citas.

Para consultas relacionadas pero no doradas, el fallback determinista debe
describir qué miembros se localizaron y pedir una reformulación si no puede
responder. Se elimina la frase fija “Se localizaron fragmentos relacionados,
pero el modo sin LLM no puede establecer una conclusión más específica”.

### Fase 4: evaluación comparativa de modelos

Crear una CLI, por ejemplo `ragscate benchmark-llm`, que ejecute secuencialmente
la misma suite para cada modelo. Nunca mantener dos modelos grandes cargados a
la vez.

Conjunto:

- las diez preguntas doradas actuales;
- al menos dos paráfrasis por pregunta;
- preguntas ausentes (`numero_poliza`, símbolos inventados);
- preguntas que requieren flujo o lugares de cambio;
- casos con comentarios/código que intenten dar instrucciones al modelo;
- respuestas con evidencia insuficiente o ambigua.

Métricas:

- validez del JSON;
- porcentaje de respuestas con todos sus `evidence_ids` permitidos;
- precisión de `No localizado`;
- cobertura de términos funcionales esperados;
- alucinaciones de archivos, miembros, tablas o líneas;
- tiempo de carga en frío, tiempo caliente, tokens por segundo;
- VRAM, porcentaje GPU y memoria del proceso;
- estabilidad en tres repeticiones.

Orden de prueba:

1. `qwen2.5:7b` (línea base instalada);
2. `qwen2.5-coder:7b`;
3. `qwen3:4b`;
4. `gemma3:4b`, solo si sigue siendo necesario.

El modelo elegido será el de menor consumo que cumpla todos los controles de
evidencia y abstención. La calidad fundamentada tiene prioridad sobre una
respuesta más extensa.

### Fase 5: experiencia de demostración

Mantener la interfaz mínima y agregar únicamente:

- modelo local activo;
- estado de Ollama;
- tiempo de respuesta;
- clasificación visible antes de la explicación;
- flujo y citas expandibles ya existentes;
- mensaje claro cuando el proveedor local no está disponible.

Antes de presentar:

1. cerrar aplicaciones innecesarias y verificar RAM/swap;
2. ejecutar `ollama run <modelo>` o una consulta de calentamiento;
3. confirmar `ollama ps` con `100% GPU` y el contexto esperado;
4. iniciar RAGscate con `.env` cargado;
5. probar una pregunta dorada, una paráfrasis y `numero_poliza`;
6. conservar el reporte de evaluación y snapshot visibles.

## 5. Criterios de aceptación

- 100% de las citas se reconstruye desde el archivo original y conserva hash.
- Ninguna salida contiene archivo, miembro, tabla o línea no recuperados.
- `numero_poliza` responde `No localizado` y sin citas.
- La DataWindow externa no se presenta como una tabla SQL.
- El flujo `cb_calcular.clicked -> of_calcular -> of_calcular_cotizacion` se
  conserva.
- Las diez respuestas doradas siguen pasando sin depender del LLM.
- Todas las pruebas comparativas usan el mismo snapshot y parámetros registrados.
- El modelo final funciona completamente en GPU con el contexto elegido, o la
  desviación queda documentada como limitación real.
- La interfaz ya no muestra la frase provisional indicada por el usuario cuando
  Ollama funciona.

## 6. Configuración inicial dejada lista

El `.env` local queda configurado con:

```text
HF_HUB_OFFLINE=1
RAG_LLM_PROVIDER=ollama
RAG_LLM_MODEL=qwen2.5:7b
RAG_LLM_BASE_URL=http://127.0.0.1:11434
```

`HF_HUB_OFFLINE=1` es apropiado porque el modelo de embeddings ya está en la
caché local. En una instalación limpia se debe desactivar temporalmente durante
la primera descarga. Este archivo está ignorado por Git. Para que la aplicación
use sus valores:

```bash
set -a
source .env
set +a
uv run ragscate serve --host 127.0.0.1 --port 8000
```

Cambiar el modelo en `.env` no requiere reindexar; cambiar el modelo de
embeddings sí requiere reconstruir el índice.
