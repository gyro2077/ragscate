# Validacion final del cotizador en PowerBuilder 9.0.3

Fecha de validacion: 8 de septiembre de 2026.

## Entorno y compilacion

- Workspace abierto: `cotizador-mvp.pbw`.
- Target utilizado: `cotizador_mvp.pbt`.
- Biblioteca utilizada: `cotizador_mvp.pbl`.
- Entorno de ejecucion: PowerBuilder 9.0.3 Build 8836 dentro de WinBoat.
- `Run > Full Build Workspace`: terminado con los mensajes `Done Building target cotizador_mvp` y `Finished Full build of workspace cotizador-mvp`, sin errores mostrados.
- El evento `Open` de `cotizador_mvp` abre `w_cotizador_mvp`.

## Objetos comprobados

- `cotizador_mvp`: Application object y punto de entrada.
- `w_cotizador_mvp`: ventana, controles, validaciones y presentacion.
- `n_cotizador_reglas`: reglas, formulas, redondeo y autorizacion.
- `str_resultado_cotizacion`: estructura de intercambio de resultados.
- `d_tabla_primas_edad`: DataWindow externa sin conexion a base de datos.

## Casos validos ejecutados

1. Edad 30, categoria Bajo, descuento 0%:
   - Antes del descuento: USD 132.00.
   - Descuento: USD 0.00.
   - Subtotal: USD 132.00.
   - Impuesto: USD 19.80.
   - Prima anual: USD 151.80.
   - Cuota mensual: USD 12.65.
   - Estado: Aprobado.

2. Edad 45, categoria Medio, descuento 5%:
   - Antes del descuento: USD 138.00.
   - Descuento: USD 6.90.
   - Subtotal: USD 131.10.
   - Impuesto: USD 19.67.
   - Prima anual: USD 150.77.
   - Cuota mensual: USD 12.56.
   - Estado: Aprobado.

3. Edad 70, categoria Alto, descuento 10%:
   - Antes del descuento: USD 210.60.
   - Descuento: USD 21.06.
   - Subtotal: USD 189.54.
   - Impuesto: USD 28.43.
   - Prima anual: USD 217.97.
   - Cuota mensual: USD 18.16.
   - Estado: Requiere autorizacion.
   - Motivos mostrados: edad entre 66 y 75 anos y categoria Alto.

En los tres casos, la tabla comparativa mostro los cinco rangos de edad y se
recalculo con la categoria y el descuento ingresados.

## Entradas invalidas comprobadas

- Edad 17: rechazada por estar fuera del rango admitido.
- Edad 76: rechazada por estar fuera del rango admitido.
- Edad vacia: mensaje de dato requerido.
- Edad `abc`: rechazada porque debe ser un numero entero.
- Categoria vacia: mensaje para seleccionar Bajo, Medio o Alto.
- Descuento -1%: rechazado por estar fuera de 0% a 10%.
- Descuento 11%: rechazado por estar fuera de 0% a 10%.

## Otros comportamientos comprobados

- `Calcular` presenta el desglose, estado, explicacion y actualiza la tabla.
- `Limpiar` borra la edad, deja la categoria sin seleccion, restablece el descuento a 0, limpia los resultados y deja el estado `Sin calcular`.
- La advertencia de reglas demostrativas se muestra en rojo en la ventana.
- La DataWindow funciona sin perfil ni conexion de base de datos.

## Fuentes finales exportadas

Despues del Full Build, los cinco objetos se exportaron desde el Library Painter
a `pb-src/`:

- `cotizador_mvp.sra`
- `d_tabla_primas_edad.srd`
- `n_cotizador_reglas.sru`
- `str_resultado_cotizacion.srs`
- `w_cotizador_mvp.srw`

Las fuentes exportadas son texto ASCII con terminadores CRLF y pasan
`python3 tests/verificar_cotizador.py`. El respaldo inicial de la PBL permanece
en `backups/initial-powerbuilder-skeleton-20260908/`.
