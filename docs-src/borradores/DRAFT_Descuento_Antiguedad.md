# BORRADOR — Propuesta de Descuento por Antigüedad

**Estado: BORRADOR — Pendiente de aprobación**

## Propuesta

Se propone implementar un descuento adicional del 5% para clientes
con más de 10 años de antigüedad en Seguros de Gyro.

## Regla Propuesta

Si el cliente tiene más de 10 años como asegurado:

    descuento_antiguedad = subtotal × 0.05

Este descuento se aplicaría DESPUÉS del descuento estándar pero ANTES
del cálculo de impuestos.

## Impacto Estimado

- Afecta a: of_calcular_cotizacion en n_cotizador_reglas
- Requiere: nuevo parámetro de antigüedad del cliente
- Requiere: nueva variable idc_descuento_antiguedad en el objeto de reglas

## Justificación

Fidelizar clientes de larga trayectoria reduciendo su prima anual.

## Estado de Aprobación

Pendiente — Este documento NO ha sido aprobado.
Presentado por: Yeshua Chiliquinga — Área de Innovación
Fecha de presentación: 2024-09-10
