# Cotizador demostrativo PowerBuilder 9

Este directorio contiene un MVP didactico, sin base de datos y sin reglas reales de seguros.

## Objetos incluidos

- `str_resultado_cotizacion`: estructura que transporta todos los resultados.
- `n_cotizador_reglas`: objeto no visual que centraliza reglas, formulas y redondeo.
- `d_tabla_primas_edad`: DataWindow externa para comparar los cinco rangos de edad.
- `w_cotizador_mvp`: ventana principal con entradas, desglose, estado y tabla.
- `cotizador_mvp`: Application object cuyo evento `Open` abre la ventana.

Las fuentes importables estan en `pb-src/`. La PBL existente no se modifica desde Linux.

## Importacion en PB 9.0.3

Los cinco objetos ya fueron importados en `cotizador_mvp.pbl`, regenerados mediante
`Run > Full Build Workspace`, ejecutados y exportados nuevamente a `pb-src/` el
8 de septiembre de 2026. Estos pasos se conservan como referencia para repetir el
proceso en otra instalacion:

1. Abra `cotizador-mvp.pbw`.
2. Abra el Library Painter y seleccione `cotizador_mvp.pbl`.
3. Use `Entry > Import` e importe, en el orden de `pb-src/ORDEN_IMPORTACION.txt`, los primeros cuatro archivos.
4. Exporte primero el Application object actual si desea otro respaldo y luego importe `cotizador_mvp.sra` aceptando reemplazar `cotizador_mvp`.
5. Ejecute `Library > Regenerate` sobre `cotizador_mvp.pbl` y revise que no existan errores.
6. Ejecute la aplicacion desde PowerBuilder.

## Reglas y redondeo

- Prima base anual: USD 120.00.
- Edad: 18-25 = 1.20; 26-35 = 1.10; 36-50 = 1.00; 51-65 = 1.15; 66-75 = 1.35.
- Categoria: Bajo = 1.00; Medio = 1.15; Alto = 1.30.
- Descuento permitido: 0% a 10%.
- Impuesto demostrativo: 15%.
- Deducible fijo demostrativo: USD 250.00.
- Autorizacion: edad 66-75 y/o categoria Alto.
- Cada importe monetario se redondea a dos decimales inmediatamente despues de calcularse. La cuota mensual usa la prima anual ya redondeada y se divide para 12.

## Casos esperados

- 30 / Bajo / 0%: antes 132.00; impuesto 19.80; anual 151.80; mensual 12.65; Aprobado.
- 45 / Medio / 5%: antes 138.00; descuento 6.90; subtotal 131.10; impuesto 19.67; anual 150.77; mensual 12.56; Aprobado.
- 70 / Alto / 10%: antes 210.60; descuento 21.06; subtotal 189.54; impuesto 28.43; anual 217.97; mensual 18.16; Requiere autorizacion por edad y categoria.

## Estado de validacion

Las formulas y la integridad estatica de las fuentes se comprueban en Linux con
`python3 tests/verificar_cotizador.py`. La importacion, la ejecucion funcional de
los tres casos obligatorios, las validaciones de entrada, el boton Limpiar, la
tabla comparativa y el Full Build sin errores fueron comprobados en PowerBuilder
9.0.3 dentro de WinBoat. El detalle esta en `VALIDACION-PB9.md`.
