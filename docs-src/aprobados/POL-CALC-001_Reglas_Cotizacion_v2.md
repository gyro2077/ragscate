# POL-CALC-001 — Reglas de Cotización de Seguros v2

## 1. Alcance

Este documento define las reglas de negocio para el cálculo de cotizaciones
en el sistema cotizador de Seguros de Gyro. Aplica a todas las pólizas
emitidas a través del módulo de cotización.

## 2. Definiciones

- **Prima base**: Monto fijo inicial para cualquier cotización. Valor vigente: USD 120.00.
- **Factor de edad**: Multiplicador que ajusta la prima según el rango etario del asegurado.
- **Factor de categoría**: Multiplicador que ajusta la prima según el nivel de riesgo seleccionado.
- **Descuento**: Porcentaje aplicable sobre la prima antes de descuento. Rango permitido: 0% a 10%.
- **Subtotal**: Prima antes de descuento menos el valor del descuento.
- **Impuesto**: Porcentaje aplicado sobre el subtotal. Valor vigente: 15%.
- **Prima anual**: Subtotal más impuesto.
- **Cuota mensual**: Prima anual dividida entre 12 meses.
- **Deducible**: Monto fijo que asume el asegurado ante un siniestro. Valor vigente: USD 250.00.

## 3. Reglas de Cálculo

### 3.1 Prima antes de descuento

Se calcula multiplicando la prima base por el factor de edad y el factor de categoría:

    prima_antes_descuento = prima_base × factor_edad × factor_categoría

El resultado se redondea a dos decimales inmediatamente después del cálculo.

### 3.2 Descuento

El descuento se aplica como porcentaje sobre la prima antes de descuento:

    valor_descuento = prima_antes_descuento × porcentaje_descuento / 100

El porcentaje de descuento debe estar entre 0 y 10. Valores fuera de este rango
son rechazados por el sistema.

### 3.3 Subtotal

    subtotal = prima_antes_descuento − valor_descuento

### 3.4 Impuesto

El impuesto se calcula sobre el subtotal:

    impuesto = subtotal × idc_impuesto_porcentaje / 100

Donde idc_impuesto_porcentaje es una constante configurable centralizada
en el objeto de reglas (n_cotizador_reglas). Valor vigente: 15%.

### 3.5 Prima anual

    prima_anual = subtotal + impuesto

### 3.6 Cuota mensual

    cuota_mensual = prima_anual / 12

### 3.7 Criterio de redondeo

Cada importe monetario se redondea a dos decimales inmediatamente después
de calcularlo. La cuota mensual usa la prima anual ya redondeada.

## 4. Validaciones de Entrada

- La edad debe ser un entero entre 18 y 75 años.
- La categoría debe ser una de: Bajo, Medio, Alto.
- El porcentaje de descuento debe ser un número entre 0 y 10.

## 5. Aprobación

Aprobado por: María Fernanda Reyes — Directora Técnica
Fecha de aprobación: 2024-08-15
Versión: 2.0
