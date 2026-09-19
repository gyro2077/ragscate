# POL-CALC-002 — Factores de Edad y Categoría

## 1. Tabla de Factores por Edad

| Rango de Edad | Factor | Justificación |
|---|---|---|
| 18 a 25 años | 1.20 | Mayor riesgo por inexperiencia |
| 26 a 35 años | 1.10 | Riesgo moderado-alto |
| 36 a 50 años | 1.00 | Riesgo base estándar |
| 51 a 65 años | 1.15 | Incremento por edad avanzada |
| 66 a 75 años | 1.35 | Alto riesgo, requiere evaluación adicional |

Edades fuera del rango 18-75 no son admitidas por el sistema.
El factor de edad retorna -1.00 para valores no admitidos, señalando rechazo.

## 2. Tabla de Factores por Categoría

| Categoría | Factor | Descripción |
|---|---|---|
| Bajo | 1.00 | Riesgo bajo, prima estándar |
| Medio | 1.15 | Riesgo intermedio |
| Alto | 1.30 | Alto riesgo, evaluación complementaria |

Categorías no reconocidas retornan -1.00, señalando rechazo.

## 3. Implementación Técnica

Los factores se implementan en el objeto de reglas n_cotizador_reglas
mediante las funciones of_factor_edad y of_factor_categoria.
Ambas funciones utilizan la estructura CHOOSE CASE para determinar el factor.

## 4. Aprobación

Aprobado por: Carlos Andrés Mendoza — Actuario Jefe
Fecha de aprobación: 2024-07-20
Versión: 1.0
