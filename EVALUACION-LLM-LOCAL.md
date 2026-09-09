# Evaluación local de Ollama para RAGscate

- Fecha UTC: `2026-09-09T05:17:48.654252+00:00`
- Modelo: `qwen2.5:7b`
- Snapshot: `97efe07425e0-050cc40dd611`
- Repeticiones: **3**
- Ejecuciones aprobadas: **90/90**
- Generaciones estructuradas aceptadas: **81/81**
- Citas reconstruidas: **162/162**
- Abstenciones `numero_poliza`: **9/9**
- Prueba de inyección en contexto no confiable: **aprobada**
- Ubicaciones o texto libre del LLM expuestos como `Comprobado`: **0** (contrato determinista cerrado)
- Duración media reportada por Ollama: **1642.47 ms**
- Primera generación medida (caliente; runner ya cargado): **1677.84 ms**
- Carga reportada en la primera generación: **0.85 ms**
- Media caliente posterior: **1642.03 ms**
- Velocidad media: **50.45 tok/s**

Referencia fría observada durante esta implementación con el mismo modelo,
parámetros y corpus: **9060.43 ms totales**, de los cuales **6955.07 ms** fueron
carga. Esa medición usó el snapshot anterior `c3d4774ab08c-050cc40dd611`; no se
forzó la descarga del runner para la corrida final porque RAGscate no debe cerrar
procesos de Ollama.

## Entorno

- CPU: `AMD Ryzen 9 7940HS w/ Radeon 780M Graphics`
- CPU lógicas: `16`
- Memoria: `{"MemTotal": "15550744 kB", "MemAvailable": "3091788 kB", "SwapTotal": "15550460 kB", "SwapFree": "5593444 kB"}`
- GPU: `NVIDIA GeForce RTX 4060 Laptop GPU, 8188 MiB, 4687 MiB`
- Parámetros: `{"timeout_seconds": 120.0, "num_ctx": 4096, "max_tokens": 500, "temperature": 0.0, "top_p": 0.9, "keep_alive": "10m", "think": false, "json_retries": 1}`

## Resultado por ejecución

| Repetición | Caso | Clasificación | Generación | ms | tok/s | Citas | Evidencia | Resultado |
|---:|---|---|---|---:|---:|---:|---:|---:|
| 1 | prima_anual | Comprobado | generated | 1677.84 | 50.45 | sí | sí | sí |
| 1 | prima_anual_p1 | Comprobado | generated | 1524.41 | 50.70 | sí | sí | sí |
| 1 | prima_anual_p2 | Comprobado | generated | 1512.63 | 51.11 | sí | sí | sí |
| 1 | flujo_calcular | Comprobado | generated | 1948.04 | 50.57 | sí | sí | sí |
| 1 | flujo_calcular_p1 | Comprobado | generated | 1641.56 | 50.49 | sí | sí | sí |
| 1 | flujo_calcular_p2 | Comprobado | generated | 1593.95 | 50.43 | sí | sí | sí |
| 1 | validar_edad | Comprobado | generated | 1877.06 | 51.06 | sí | sí | sí |
| 1 | validar_edad_p1 | Comprobado | generated | 1709.77 | 51.22 | sí | sí | sí |
| 1 | validar_edad_p2 | Comprobado | generated | 1510.31 | 51.02 | sí | sí | sí |
| 1 | autorizar_70_alto | Comprobado | generated | 1552.03 | 50.54 | sí | sí | sí |
| 1 | autorizar_70_alto_p1 | Comprobado | generated | 1494.53 | 51.49 | sí | sí | sí |
| 1 | autorizar_70_alto_p2 | Comprobado | generated | 1498.18 | 51.32 | sí | sí | sí |
| 1 | cambiar_impuesto | Comprobado | generated | 1635.72 | 51.23 | sí | sí | sí |
| 1 | cambiar_impuesto_p1 | Comprobado | generated | 1667.28 | 50.29 | sí | sí | sí |
| 1 | cambiar_impuesto_p2 | Comprobado | generated | 1648.36 | 51.18 | sí | sí | sí |
| 1 | agregar_categoria | Comprobado | generated | 1629.80 | 51.09 | sí | sí | sí |
| 1 | agregar_categoria_p1 | Comprobado | generated | 1698.14 | 51.28 | sí | sí | sí |
| 1 | agregar_categoria_p2 | Comprobado | generated | 1724.09 | 50.60 | sí | sí | sí |
| 1 | tabla_datawindow | Comprobado | generated | 1869.85 | 50.66 | sí | sí | sí |
| 1 | tabla_datawindow_p1 | Comprobado | generated | 1543.95 | 51.03 | sí | sí | sí |
| 1 | tabla_datawindow_p2 | Comprobado | generated | 1520.62 | 50.87 | sí | sí | sí |
| 1 | cuota_mensual | Comprobado | generated | 1630.85 | 50.87 | sí | sí | sí |
| 1 | cuota_mensual_p1 | Comprobado | generated | 1528.25 | 50.48 | sí | sí | sí |
| 1 | cuota_mensual_p2 | Comprobado | generated | 1504.11 | 51.39 | sí | sí | sí |
| 1 | limpiar | Comprobado | generated | 1586.85 | 51.32 | sí | sí | sí |
| 1 | limpiar_p1 | Comprobado | generated | 1587.34 | 51.24 | sí | sí | sí |
| 1 | limpiar_p2 | Comprobado | generated | 1628.46 | 49.91 | sí | sí | sí |
| 1 | simbolo_ausente | No localizado | not_invoked | no disponible | no disponible | sí | sí | sí |
| 1 | simbolo_ausente_p1 | No localizado | not_invoked | no disponible | no disponible | sí | sí | sí |
| 1 | simbolo_ausente_p2 | No localizado | not_invoked | no disponible | no disponible | sí | sí | sí |
| 2 | prima_anual | Comprobado | generated | 1501.46 | 51.53 | sí | sí | sí |
| 2 | prima_anual_p1 | Comprobado | generated | 1507.66 | 51.37 | sí | sí | sí |
| 2 | prima_anual_p2 | Comprobado | generated | 1505.77 | 51.29 | sí | sí | sí |
| 2 | flujo_calcular | Comprobado | generated | 1976.17 | 50.02 | sí | sí | sí |
| 2 | flujo_calcular_p1 | Comprobado | generated | 1543.35 | 50.38 | sí | sí | sí |
| 2 | flujo_calcular_p2 | Comprobado | generated | 1586.27 | 50.97 | sí | sí | sí |
| 2 | validar_edad | Comprobado | generated | 1859.76 | 50.99 | sí | sí | sí |
| 2 | validar_edad_p1 | Comprobado | generated | 1762.67 | 50.22 | sí | sí | sí |
| 2 | validar_edad_p2 | Comprobado | generated | 1518.20 | 50.50 | sí | sí | sí |
| 2 | autorizar_70_alto | Comprobado | generated | 1559.77 | 51.12 | sí | sí | sí |
| 2 | autorizar_70_alto_p1 | Comprobado | generated | 1543.48 | 50.70 | sí | sí | sí |
| 2 | autorizar_70_alto_p2 | Comprobado | generated | 1527.70 | 51.02 | sí | sí | sí |
| 2 | cambiar_impuesto | Comprobado | generated | 1674.37 | 50.15 | sí | sí | sí |
| 2 | cambiar_impuesto_p1 | Comprobado | generated | 1673.55 | 50.80 | sí | sí | sí |
| 2 | cambiar_impuesto_p2 | Comprobado | generated | 1672.43 | 50.87 | sí | sí | sí |
| 2 | agregar_categoria | Comprobado | generated | 1654.11 | 51.09 | sí | sí | sí |
| 2 | agregar_categoria_p1 | Comprobado | generated | 1765.58 | 49.75 | sí | sí | sí |
| 2 | agregar_categoria_p2 | Comprobado | generated | 1755.65 | 50.52 | sí | sí | sí |
| 2 | tabla_datawindow | Comprobado | generated | 1894.19 | 50.59 | sí | sí | sí |
| 2 | tabla_datawindow_p1 | Comprobado | generated | 1462.45 | 50.67 | sí | sí | sí |
| 2 | tabla_datawindow_p2 | Comprobado | generated | 1539.51 | 49.82 | sí | sí | sí |
| 2 | cuota_mensual | Comprobado | generated | 1603.76 | 50.67 | sí | sí | sí |
| 2 | cuota_mensual_p1 | Comprobado | generated | 1536.88 | 51.05 | sí | sí | sí |
| 2 | cuota_mensual_p2 | Comprobado | generated | 1523.47 | 51.01 | sí | sí | sí |
| 2 | limpiar | Comprobado | generated | 1628.05 | 50.51 | sí | sí | sí |
| 2 | limpiar_p1 | Comprobado | generated | 1641.04 | 50.23 | sí | sí | sí |
| 2 | limpiar_p2 | Comprobado | generated | 1647.41 | 50.02 | sí | sí | sí |
| 2 | simbolo_ausente | No localizado | not_invoked | no disponible | no disponible | sí | sí | sí |
| 2 | simbolo_ausente_p1 | No localizado | not_invoked | no disponible | no disponible | sí | sí | sí |
| 2 | simbolo_ausente_p2 | No localizado | not_invoked | no disponible | no disponible | sí | sí | sí |
| 3 | prima_anual | Comprobado | generated | 1536.37 | 50.99 | sí | sí | sí |
| 3 | prima_anual_p1 | Comprobado | generated | 1522.95 | 50.88 | sí | sí | sí |
| 3 | prima_anual_p2 | Comprobado | generated | 1592.45 | 49.33 | sí | sí | sí |
| 3 | flujo_calcular | Comprobado | generated | 2019.73 | 50.13 | sí | sí | sí |
| 3 | flujo_calcular_p1 | Comprobado | generated | 1560.09 | 50.20 | sí | sí | sí |
| 3 | flujo_calcular_p2 | Comprobado | generated | 1611.12 | 50.29 | sí | sí | sí |
| 3 | validar_edad | Comprobado | generated | 1931.58 | 48.96 | sí | sí | sí |
| 3 | validar_edad_p1 | Comprobado | generated | 1744.00 | 50.30 | sí | sí | sí |
| 3 | validar_edad_p2 | Comprobado | generated | 1572.65 | 50.05 | sí | sí | sí |
| 3 | autorizar_70_alto | Comprobado | generated | 1580.56 | 50.42 | sí | sí | sí |
| 3 | autorizar_70_alto_p1 | Comprobado | generated | 1607.32 | 48.72 | sí | sí | sí |
| 3 | autorizar_70_alto_p2 | Comprobado | generated | 1589.44 | 49.39 | sí | sí | sí |
| 3 | cambiar_impuesto | Comprobado | generated | 1724.28 | 49.51 | sí | sí | sí |
| 3 | cambiar_impuesto_p1 | Comprobado | generated | 1715.47 | 49.29 | sí | sí | sí |
| 3 | cambiar_impuesto_p2 | Comprobado | generated | 1741.82 | 48.96 | sí | sí | sí |
| 3 | agregar_categoria | Comprobado | generated | 1693.68 | 49.43 | sí | sí | sí |
| 3 | agregar_categoria_p1 | Comprobado | generated | 1797.46 | 49.27 | sí | sí | sí |
| 3 | agregar_categoria_p2 | Comprobado | generated | 1750.38 | 50.02 | sí | sí | sí |
| 3 | tabla_datawindow | Comprobado | generated | 1978.65 | 48.78 | sí | sí | sí |
| 3 | tabla_datawindow_p1 | Comprobado | generated | 1474.34 | 50.00 | sí | sí | sí |
| 3 | tabla_datawindow_p2 | Comprobado | generated | 1539.52 | 50.16 | sí | sí | sí |
| 3 | cuota_mensual | Comprobado | generated | 1613.11 | 50.63 | sí | sí | sí |
| 3 | cuota_mensual_p1 | Comprobado | generated | 1577.75 | 49.84 | sí | sí | sí |
| 3 | cuota_mensual_p2 | Comprobado | generated | 1581.80 | 49.72 | sí | sí | sí |
| 3 | limpiar | Comprobado | generated | 1661.06 | 49.68 | sí | sí | sí |
| 3 | limpiar_p1 | Comprobado | generated | 1657.12 | 49.99 | sí | sí | sí |
| 3 | limpiar_p2 | Comprobado | generated | 1656.99 | 49.76 | sí | sí | sí |
| 3 | simbolo_ausente | No localizado | not_invoked | no disponible | no disponible | sí | sí | sí |
| 3 | simbolo_ausente_p1 | No localizado | not_invoked | no disponible | no disponible | sí | sí | sí |
| 3 | simbolo_ausente_p2 | No localizado | not_invoked | no disponible | no disponible | sí | sí | sí |

## Rechazos y fallos

Ninguno.

## Validación end-to-end manual

- Pregunta abierta no codificada como intención fija: respuesta `Inferido`,
  generación local aceptada y dos citas validadas.
- Pregunta compuesta de flujo, validaciones, prima e impuesto: respuesta
  `Comprobado`, cinco citas y acuse JSON aceptado en un intento.
- `numero_poliza`: `No localizado`, cero citas y `generation.status=not_invoked`.
- `GET /api/source/{chunk_id}` reconstruyó desde el original las líneas 91-103
  de `of_calcular_cotizacion`.
- La interfaz se abrió en navegador, mostró el modelo y snapshot activos y
  expandió la cita de `of_calcular_cotizacion` con su texto original.

## `ollama ps` al finalizar

```text
NAME          ID              SIZE      PROCESSOR    CONTEXT    UNTIL              
qwen2.5:7b    845dbda0ea48    4.7 GB    100% GPU     4096       9 minutes from now
```

El benchmark no descarga modelos ni altera el corpus. Las citas se vuelven a reconstruir desde los SR* originales en cada caso.
