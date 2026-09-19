# POL-CALC-003 — Condiciones de Autorización Especial

## 1. Condiciones que Requieren Autorización

Una cotización requiere autorización especial cuando se cumple al menos
una de las siguientes condiciones:

- **Edad avanzada**: El asegurado tiene 66 años o más (ai_edad >= 66).
- **Categoría de alto riesgo**: La categoría seleccionada es "Alto".

Cuando ambas condiciones se cumplen simultáneamente, el motivo registrado
debe indicar ambas causas.

## 2. Estados Posibles

| Estado | Condición |
|---|---|
| Aprobado | Ninguna condición de autorización se cumple |
| Requiere autorización | Al menos una condición se cumple |

## 3. Motivos de Autorización

- Solo edad: "Edad entre 66 y 75 anos."
- Solo categoría: "Categoria Alto."
- Ambos: "Edad entre 66 y 75 anos y categoria Alto."
- Ninguno: "No aplica."

## 4. Implementación Técnica

La evaluación se realiza en la función of_calcular_cotizacion del objeto
n_cotizador_reglas, después de completar todos los cálculos de prima.
Las variables lb_autoriza_edad y lb_autoriza_categoria determinan el resultado.

## 5. Aprobación

Aprobado por: Roberto Salazar — Gerente de Riesgos
Fecha de aprobación: 2024-09-01
Versión: 1.0
