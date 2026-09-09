# Mapa didactico del codigo

Las lineas indicadas corresponden a las fuentes actuales en `pb-src/`. PowerBuilder puede reordenar o reformatear algunas lineas al volver a exportar.

## Reglas de negocio

- `pb-src/n_cotizador_reglas.sru:13`: constantes configurables del MVP.
- `pb-src/n_cotizador_reglas.sru:25`: seleccion del factor por rango de edad.
- `pb-src/n_cotizador_reglas.sru:43`: seleccion del factor por categoria.
- `pb-src/n_cotizador_reglas.sru:60`: validacion defensiva y calculo completo.
- `pb-src/n_cotizador_reglas.sru:91`: formula y redondeo de importes.
- `pb-src/n_cotizador_reglas.sru:104`: reglas de autorizacion y sus motivos.

## Interfaz

- `pb-src/w_cotizador_mvp.srw:151`: lectura y validacion de los tres datos de entrada.
- `pb-src/w_cotizador_mvp.srw:214`: presentacion del desglose.
- `pb-src/w_cotizador_mvp.srw:229`: recalculo de la tabla por edades.
- `pb-src/w_cotizador_mvp.srw:271`: coordinacion del boton Calcular.
- `pb-src/w_cotizador_mvp.srw:289`: limpieza del formulario.
- `pb-src/w_cotizador_mvp.srw:408`: inicializacion de la ventana.
- `pb-src/w_cotizador_mvp.srw:576`: evento del boton Calcular.
- `pb-src/w_cotizador_mvp.srw:597`: evento del boton Limpiar.

## Datos y arranque

- `pb-src/str_resultado_cotizacion.srs:3`: contrato de resultados entre reglas e interfaz.
- `pb-src/d_tabla_primas_edad.srd:9`: definicion de las cinco columnas externas.
- `pb-src/cotizador_mvp.sra:38`: evento Open que abre `w_cotizador_mvp`.
