# LIN-SEC-001 — Lineamientos de Seguridad Aplicativa

## 1. Validación de Entradas

### 1.1 Principio general

Nunca confiar en datos proporcionados por la interfaz de usuario.
Toda validación debe duplicarse en la capa de reglas de negocio.

### 1.2 Validación numérica

Todo valor numérico ingresado por el usuario debe verificarse:
- Que sea numérico (IsNumber)
- Que esté dentro del rango permitido
- Que sea entero cuando se espera entero (no aceptar decimales para edad)

### 1.3 Validación de rangos

Los porcentajes deben validarse entre 0 y su máximo permitido.
Las edades deben validarse entre 18 y 75.
Los factores no deben ser negativos en uso normal.

## 2. Manejo de Errores

### 2.1 Mensajes de error

Los mensajes deben ser descriptivos pero no revelar detalles de implementación.
Correcto: "La edad admitida debe estar entre 18 y 75 años."
Incorrecto: "Error en of_factor_edad: CHOOSE CASE no matcheó."

### 2.2 Estado consistente

Ante un error de validación, el estado del resultado debe ser consistente:
- es_valido = false
- mensaje_error contiene la descripción
- Los campos numéricos conservan sus valores iniciales (0)

## 3. Aprobación

Aprobado por: Diana Estrella — CISO
Fecha de aprobación: 2024-05-15
Versión: 1.0
