# RAGscate

**RAGscate** es un MVP educativo para investigar como un asistente RAG puede
ayudar a comprender codigo PowerBuilder legado mediante respuestas respaldadas
por fragmentos verificables.

El repositorio usa un cotizador completamente didactico como corpus de ejemplo.
No contiene codigo, datos, tarifas ni reglas reales de una aseguradora.

## Objetivo del MVP

El asistente buscado debe poder responder preguntas como:

- ¿Donde se calcula la prima anual?
- ¿Que validaciones ejecuta el boton Calcular?
- ¿Por que una cotizacion requiere autorizacion?
- ¿Que objeto tendria que revisarse para cambiar una regla?

Cada respuesta debera identificar, cuando exista evidencia suficiente:

- biblioteca y archivo fuente;
- objeto PowerBuilder;
- evento o funcion;
- rango de lineas;
- version del codigo;
- clasificacion `Comprobado`, `Inferido` o `No localizado`.

El modelo explicara el codigo recuperado. No calculara primas oficiales, no
modificara fuentes automaticamente y no reemplazara la validacion realizada en
PowerBuilder.

## Estado actual

### Completado: corpus PowerBuilder demostrativo

- Aplicacion didactica creada en PowerBuilder 9.0.3 Build 8836.
- Cinco objetos exportados a fuentes de texto `SR*`.
- Reglas centralizadas en un objeto no visual.
- Interfaz con validaciones, desglose y tabla comparativa.
- Tres casos validos y rutas de error comprobadas.
- Full Build y ejecucion funcional registrados en `VALIDACION-PB9.md`.
- Verificacion estructural y matematica ejecutable desde Linux.

### Pendiente: asistente RAG

- Ingesta de las fuentes exportadas.
- Segmentacion por objeto, funcion y evento.
- Busqueda exacta y semantica.
- Respuestas con citas verificables.
- Interfaz minima de preguntas y fragmentos recuperados.
- Evaluacion con un conjunto pequeno de preguntas conocidas.

Por tanto, este repositorio contiene actualmente el **codigo legacy de ejemplo
validado**, no una implementacion terminada del asistente RAG.

## Estructura

```text
.
├── cotizador-mvp.pbw          # Workspace PowerBuilder
├── cotizador_mvp.pbt          # Target PowerBuilder
├── cotizador_mvp.pbl          # Biblioteca didactica compilable
├── pb-src/                    # Objetos PowerBuilder exportados como texto
├── tests/                     # Verificacion independiente en Linux
├── README-COTIZADOR-PB9.md    # Uso del cotizador
├── MAPA-CODIGO-COTIZADOR.md   # Guia de objetos, eventos y funciones
└── VALIDACION-PB9.md          # Evidencia de compilacion y ejecucion
```

## Verificacion desde Linux

```bash
python3 tests/verificar_cotizador.py
```

La prueba confirma la presencia y consistencia basica de las fuentes, reproduce
los tres resultados esperados y comprueba las entradas invalidas contempladas.
No sustituye la compilacion ni las pruebas funcionales en PowerBuilder.

## PowerBuilder y Linux

PowerBuilder es software propietario y no se distribuye en este repositorio.
Las imagenes de instalacion, parches y licencias deben obtenerse por canales
autorizados.

El cotizador fue compilado y ejecutado con PowerBuilder 9.0.3 dentro de un
entorno Windows administrado desde Linux mediante WinBoat. Esto no significa
que PowerBuilder sea una aplicacion nativa de Linux ni confirma compatibilidad
directa con Wine.

## Alcance de seguridad y privacidad

- No hay conexion a base de datos.
- No se incluyen secretos ni credenciales.
- Las formulas son ficticias y estan marcadas como demostrativas.
- No se incluyen archivos empresariales ni codigo de produccion.
- Las ISO de PowerBuilder estan excluidas deliberadamente del control de
  versiones.

## Nombre

RAGscate combina **RAG** y **rescate**: recuperar conocimiento tecnico atrapado
en aplicaciones legadas sin presentar inferencias del modelo como hechos.

## Licencia

El codigo propio de RAGscate se publica bajo la GNU Affero General Public
License v3.0 incluida en `LICENSE`. PowerBuilder y sus componentes mantienen las
licencias de sus respectivos propietarios y no forman parte de esta
distribucion.
