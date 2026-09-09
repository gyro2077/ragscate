$PBExportHeader$w_cotizador_mvp.srw
$PBExportComments$Ventana principal didactica del cotizador MVP
forward
global type w_cotizador_mvp from window
end type
type st_titulo from statictext within w_cotizador_mvp
end type
type st_advertencia from statictext within w_cotizador_mvp
end type
type st_datos from statictext within w_cotizador_mvp
end type
type st_edad_etiqueta from statictext within w_cotizador_mvp
end type
type sle_edad from singlelineedit within w_cotizador_mvp
end type
type st_categoria_etiqueta from statictext within w_cotizador_mvp
end type
type ddlb_categoria from dropdownlistbox within w_cotizador_mvp
end type
type st_descuento_etiqueta from statictext within w_cotizador_mvp
end type
type sle_descuento from singlelineedit within w_cotizador_mvp
end type
type cb_calcular from commandbutton within w_cotizador_mvp
end type
type cb_limpiar from commandbutton within w_cotizador_mvp
end type
type st_desglose from statictext within w_cotizador_mvp
end type
type st_prima_base_etiqueta from statictext within w_cotizador_mvp
end type
type st_prima_base_valor from statictext within w_cotizador_mvp
end type
type st_factor_edad_etiqueta from statictext within w_cotizador_mvp
end type
type st_factor_edad_valor from statictext within w_cotizador_mvp
end type
type st_factor_categoria_etiqueta from statictext within w_cotizador_mvp
end type
type st_factor_categoria_valor from statictext within w_cotizador_mvp
end type
type st_antes_descuento_etiqueta from statictext within w_cotizador_mvp
end type
type st_antes_descuento_valor from statictext within w_cotizador_mvp
end type
type st_descuento_valor_etiqueta from statictext within w_cotizador_mvp
end type
type st_descuento_valor from statictext within w_cotizador_mvp
end type
type st_subtotal_etiqueta from statictext within w_cotizador_mvp
end type
type st_subtotal_valor from statictext within w_cotizador_mvp
end type
type st_impuesto_etiqueta from statictext within w_cotizador_mvp
end type
type st_impuesto_valor from statictext within w_cotizador_mvp
end type
type st_deducible_etiqueta from statictext within w_cotizador_mvp
end type
type st_deducible_valor from statictext within w_cotizador_mvp
end type
type st_prima_anual_etiqueta from statictext within w_cotizador_mvp
end type
type st_prima_anual from statictext within w_cotizador_mvp
end type
type st_cuota_mensual_etiqueta from statictext within w_cotizador_mvp
end type
type st_cuota_mensual from statictext within w_cotizador_mvp
end type
type st_estado_etiqueta from statictext within w_cotizador_mvp
end type
type st_estado from statictext within w_cotizador_mvp
end type
type st_explicacion_etiqueta from statictext within w_cotizador_mvp
end type
type mle_explicacion from multilineedit within w_cotizador_mvp
end type
type st_tabla_titulo from statictext within w_cotizador_mvp
end type
type dw_tabla_edades from datawindow within w_cotizador_mvp
end type
end forward

global type w_cotizador_mvp from window
integer width = 6000
integer height = 4300
boolean titlebar = true
string title = "Cotizador demostrativo"
boolean controlmenu = true
boolean minbox = true
boolean maxbox = true
boolean resizable = false
long backcolor = 67108864
string icon = "AppIcon!"
boolean center = true
st_titulo st_titulo
st_advertencia st_advertencia
st_datos st_datos
st_edad_etiqueta st_edad_etiqueta
sle_edad sle_edad
st_categoria_etiqueta st_categoria_etiqueta
ddlb_categoria ddlb_categoria
st_descuento_etiqueta st_descuento_etiqueta
sle_descuento sle_descuento
cb_calcular cb_calcular
cb_limpiar cb_limpiar
st_desglose st_desglose
st_prima_base_etiqueta st_prima_base_etiqueta
st_prima_base_valor st_prima_base_valor
st_factor_edad_etiqueta st_factor_edad_etiqueta
st_factor_edad_valor st_factor_edad_valor
st_factor_categoria_etiqueta st_factor_categoria_etiqueta
st_factor_categoria_valor st_factor_categoria_valor
st_antes_descuento_etiqueta st_antes_descuento_etiqueta
st_antes_descuento_valor st_antes_descuento_valor
st_descuento_valor_etiqueta st_descuento_valor_etiqueta
st_descuento_valor st_descuento_valor
st_subtotal_etiqueta st_subtotal_etiqueta
st_subtotal_valor st_subtotal_valor
st_impuesto_etiqueta st_impuesto_etiqueta
st_impuesto_valor st_impuesto_valor
st_deducible_etiqueta st_deducible_etiqueta
st_deducible_valor st_deducible_valor
st_prima_anual_etiqueta st_prima_anual_etiqueta
st_prima_anual st_prima_anual
st_cuota_mensual_etiqueta st_cuota_mensual_etiqueta
st_cuota_mensual st_cuota_mensual
st_estado_etiqueta st_estado_etiqueta
st_estado st_estado
st_explicacion_etiqueta st_explicacion_etiqueta
mle_explicacion mle_explicacion
st_tabla_titulo st_tabla_titulo
dw_tabla_edades dw_tabla_edades
end type
global w_cotizador_mvp w_cotizador_mvp

type prototypes
end prototypes

type variables
private n_cotizador_reglas inv_reglas
end variables

forward prototypes
public function boolean of_leer_entradas (ref integer ai_edad, ref string as_categoria, ref decimal adc_descuento)
public subroutine of_mostrar_resultado (str_resultado_cotizacion astr_resultado)
public subroutine of_actualizar_tabla (string as_categoria, decimal adc_descuento)
public subroutine of_calcular ()
public subroutine of_limpiar ()
end prototypes

public function boolean of_leer_entradas (ref integer ai_edad, ref string as_categoria, ref decimal adc_descuento);
string ls_edad
string ls_descuento
decimal ldec_edad

ls_edad = trim(sle_edad.text)
if ls_edad = "" then
	messagebox("Dato requerido", "Ingrese la edad de la persona.", Exclamation!)
	sle_edad.setfocus()
	return false
end if

if not isnumber(ls_edad) then
	messagebox("Edad no valida", "La edad debe ser un numero entero.", Exclamation!)
	sle_edad.setfocus()
	return false
end if

ldec_edad = dec(ls_edad)
if ldec_edad <> round(ldec_edad, 0) then
	messagebox("Edad no valida", "La edad debe ser un numero entero.", Exclamation!)
	sle_edad.setfocus()
	return false
end if

ai_edad = integer(ldec_edad)
if ai_edad < 18 or ai_edad > 75 then
	messagebox("Edad no admitida", "La edad admitida debe estar entre 18 y 75 a~hF1os.", Exclamation!)
	sle_edad.setfocus()
	return false
end if

as_categoria = trim(ddlb_categoria.text)
if as_categoria = "" then
	messagebox("Dato requerido", "Seleccione la categoria Bajo, Medio o Alto.", Exclamation!)
	ddlb_categoria.setfocus()
	return false
end if

ls_descuento = trim(sle_descuento.text)
if ls_descuento = "" then
	messagebox("Dato requerido", "Ingrese el porcentaje de descuento.", Exclamation!)
	sle_descuento.setfocus()
	return false
end if

if not isnumber(ls_descuento) then
	messagebox("Descuento no valido", "El descuento debe ser un numero entre 0 y 10.", Exclamation!)
	sle_descuento.setfocus()
	return false
end if

adc_descuento = dec(ls_descuento)
if adc_descuento < 0 or adc_descuento > 10 then
	messagebox("Descuento no valido", "El descuento permitido esta entre 0 y 10 por ciento.", Exclamation!)
	sle_descuento.setfocus()
	return false
end if

return true
end function

public subroutine of_mostrar_resultado (str_resultado_cotizacion astr_resultado);
st_prima_base_valor.text = "USD " + string(astr_resultado.prima_base, "#,##0.00")
st_factor_edad_valor.text = string(astr_resultado.factor_edad, "0.00")
st_factor_categoria_valor.text = string(astr_resultado.factor_categoria, "0.00")
st_antes_descuento_valor.text = "USD " + string(astr_resultado.prima_antes_descuento, "#,##0.00")
st_descuento_valor.text = "USD " + string(astr_resultado.valor_descuento, "#,##0.00")
st_subtotal_valor.text = "USD " + string(astr_resultado.subtotal, "#,##0.00")
st_impuesto_valor.text = "USD " + string(astr_resultado.impuesto, "#,##0.00")
st_deducible_valor.text = "USD " + string(astr_resultado.deducible, "#,##0.00")
st_prima_anual.text = "USD " + string(astr_resultado.prima_anual, "#,##0.00")
st_cuota_mensual.text = "USD " + string(astr_resultado.cuota_mensual, "#,##0.00")
st_estado.text = astr_resultado.estado
mle_explicacion.text = astr_resultado.explicacion
end subroutine

public subroutine of_actualizar_tabla (string as_categoria, decimal adc_descuento);
integer li_indice
integer li_fila
integer li_edades[5]
string ls_rangos[5]
string ls_condicion
str_resultado_cotizacion lstr_resultado

li_edades[1] = 21
li_edades[2] = 30
li_edades[3] = 43
li_edades[4] = 58
li_edades[5] = 70
ls_rangos[1] = "18 a 25"
ls_rangos[2] = "26 a 35"
ls_rangos[3] = "36 a 50"
ls_rangos[4] = "51 a 65"
ls_rangos[5] = "66 a 75"

dw_tabla_edades.setredraw(false)
dw_tabla_edades.reset()

for li_indice = 1 to 5
	lstr_resultado = inv_reglas.of_calcular_cotizacion(li_edades[li_indice], &
		as_categoria, adc_descuento)
	if lstr_resultado.es_valido then
		li_fila = dw_tabla_edades.insertrow(0)
		dw_tabla_edades.setitem(li_fila, "rango_edad", ls_rangos[li_indice])
		dw_tabla_edades.setitem(li_fila, "factor_edad", lstr_resultado.factor_edad)
		dw_tabla_edades.setitem(li_fila, "prima_anual", lstr_resultado.prima_anual)
		dw_tabla_edades.setitem(li_fila, "cuota_mensual", lstr_resultado.cuota_mensual)
		ls_condicion = lstr_resultado.estado
		if lstr_resultado.estado = "Requiere autorizacion" then
			ls_condicion = ls_condicion + ": " + lstr_resultado.motivos_autorizacion
		end if
		dw_tabla_edades.setitem(li_fila, "condicion", ls_condicion)
	end if
next

dw_tabla_edades.setredraw(true)
end subroutine

public subroutine of_calcular ();
integer li_edad
string ls_categoria
decimal ldec_descuento
str_resultado_cotizacion lstr_resultado

if not of_leer_entradas(li_edad, ls_categoria, ldec_descuento) then return

lstr_resultado = inv_reglas.of_calcular_cotizacion(li_edad, ls_categoria, ldec_descuento)
if not lstr_resultado.es_valido then
	messagebox("No se pudo calcular", lstr_resultado.mensaje_error, Exclamation!)
	return
end if

of_mostrar_resultado(lstr_resultado)
of_actualizar_tabla(ls_categoria, ldec_descuento)
end subroutine

public subroutine of_limpiar ();
sle_edad.text = ""
// El indice cero limpia la seleccion y permite validar categoria obligatoria.
ddlb_categoria.selectitem(0)
sle_descuento.text = "0"
st_prima_base_valor.text = "-"
st_factor_edad_valor.text = "-"
st_factor_categoria_valor.text = "-"
st_antes_descuento_valor.text = "-"
st_descuento_valor.text = "-"
st_subtotal_valor.text = "-"
st_impuesto_valor.text = "-"
st_deducible_valor.text = "-"
st_prima_anual.text = "-"
st_cuota_mensual.text = "-"
st_estado.text = "Sin calcular"
mle_explicacion.text = "Ingrese los datos y presione Calcular."
of_actualizar_tabla("Bajo", 0)
sle_edad.setfocus()
end subroutine

on w_cotizador_mvp.create
this.st_titulo = create st_titulo
this.st_advertencia = create st_advertencia
this.st_datos = create st_datos
this.st_edad_etiqueta = create st_edad_etiqueta
this.sle_edad = create sle_edad
this.st_categoria_etiqueta = create st_categoria_etiqueta
this.ddlb_categoria = create ddlb_categoria
this.st_descuento_etiqueta = create st_descuento_etiqueta
this.sle_descuento = create sle_descuento
this.cb_calcular = create cb_calcular
this.cb_limpiar = create cb_limpiar
this.st_desglose = create st_desglose
this.st_prima_base_etiqueta = create st_prima_base_etiqueta
this.st_prima_base_valor = create st_prima_base_valor
this.st_factor_edad_etiqueta = create st_factor_edad_etiqueta
this.st_factor_edad_valor = create st_factor_edad_valor
this.st_factor_categoria_etiqueta = create st_factor_categoria_etiqueta
this.st_factor_categoria_valor = create st_factor_categoria_valor
this.st_antes_descuento_etiqueta = create st_antes_descuento_etiqueta
this.st_antes_descuento_valor = create st_antes_descuento_valor
this.st_descuento_valor_etiqueta = create st_descuento_valor_etiqueta
this.st_descuento_valor = create st_descuento_valor
this.st_subtotal_etiqueta = create st_subtotal_etiqueta
this.st_subtotal_valor = create st_subtotal_valor
this.st_impuesto_etiqueta = create st_impuesto_etiqueta
this.st_impuesto_valor = create st_impuesto_valor
this.st_deducible_etiqueta = create st_deducible_etiqueta
this.st_deducible_valor = create st_deducible_valor
this.st_prima_anual_etiqueta = create st_prima_anual_etiqueta
this.st_prima_anual = create st_prima_anual
this.st_cuota_mensual_etiqueta = create st_cuota_mensual_etiqueta
this.st_cuota_mensual = create st_cuota_mensual
this.st_estado_etiqueta = create st_estado_etiqueta
this.st_estado = create st_estado
this.st_explicacion_etiqueta = create st_explicacion_etiqueta
this.mle_explicacion = create mle_explicacion
this.st_tabla_titulo = create st_tabla_titulo
this.dw_tabla_edades = create dw_tabla_edades
this.control[] = {this.st_titulo, &
	this.st_advertencia, this.st_datos, this.st_edad_etiqueta, this.sle_edad, &
	this.st_categoria_etiqueta, this.ddlb_categoria, this.st_descuento_etiqueta, &
	this.sle_descuento, this.cb_calcular, this.cb_limpiar, this.st_desglose, &
	this.st_prima_base_etiqueta, this.st_prima_base_valor, &
	this.st_factor_edad_etiqueta, this.st_factor_edad_valor, &
	this.st_factor_categoria_etiqueta, this.st_factor_categoria_valor, &
	this.st_antes_descuento_etiqueta, this.st_antes_descuento_valor, &
	this.st_descuento_valor_etiqueta, this.st_descuento_valor, &
	this.st_subtotal_etiqueta, this.st_subtotal_valor, &
	this.st_impuesto_etiqueta, this.st_impuesto_valor, &
	this.st_deducible_etiqueta, this.st_deducible_valor, &
	this.st_prima_anual_etiqueta, this.st_prima_anual, &
	this.st_cuota_mensual_etiqueta, this.st_cuota_mensual, &
	this.st_estado_etiqueta, this.st_estado, this.st_explicacion_etiqueta, &
	this.mle_explicacion, this.st_tabla_titulo, this.dw_tabla_edades}
end on

on w_cotizador_mvp.destroy
destroy(this.st_titulo)
destroy(this.st_advertencia)
destroy(this.st_datos)
destroy(this.st_edad_etiqueta)
destroy(this.sle_edad)
destroy(this.st_categoria_etiqueta)
destroy(this.ddlb_categoria)
destroy(this.st_descuento_etiqueta)
destroy(this.sle_descuento)
destroy(this.cb_calcular)
destroy(this.cb_limpiar)
destroy(this.st_desglose)
destroy(this.st_prima_base_etiqueta)
destroy(this.st_prima_base_valor)
destroy(this.st_factor_edad_etiqueta)
destroy(this.st_factor_edad_valor)
destroy(this.st_factor_categoria_etiqueta)
destroy(this.st_factor_categoria_valor)
destroy(this.st_antes_descuento_etiqueta)
destroy(this.st_antes_descuento_valor)
destroy(this.st_descuento_valor_etiqueta)
destroy(this.st_descuento_valor)
destroy(this.st_subtotal_etiqueta)
destroy(this.st_subtotal_valor)
destroy(this.st_impuesto_etiqueta)
destroy(this.st_impuesto_valor)
destroy(this.st_deducible_etiqueta)
destroy(this.st_deducible_valor)
destroy(this.st_prima_anual_etiqueta)
destroy(this.st_prima_anual)
destroy(this.st_cuota_mensual_etiqueta)
destroy(this.st_cuota_mensual)
destroy(this.st_estado_etiqueta)
destroy(this.st_estado)
destroy(this.st_explicacion_etiqueta)
destroy(this.mle_explicacion)
destroy(this.st_tabla_titulo)
destroy(this.dw_tabla_edades)
end on

event open;
inv_reglas = create n_cotizador_reglas
ddlb_categoria.additem("Bajo")
ddlb_categoria.additem("Medio")
ddlb_categoria.additem("Alto")
of_limpiar()
end event

event close;
if isvalid(inv_reglas) then destroy inv_reglas
end event

type st_titulo from statictext within w_cotizador_mvp
integer x = 160
integer y = 48
integer width = 5600
integer height = 120
integer textsize = -16
integer weight = 700
fontcharset fontcharset = ansi!
fontfamily fontfamily = swiss!
fontpitch fontpitch = variable!
string facename = "Arial"
string text = "Cotizador demostrativo"
alignment alignment = center!
long textcolor = 0
long backcolor = 67108864
end type

type st_advertencia from statictext within w_cotizador_mvp
integer x = 160
integer y = 180
integer width = 5600
integer height = 100
integer textsize = -10
integer weight = 700
fontcharset fontcharset = ansi!
fontfamily fontfamily = swiss!
fontpitch fontpitch = variable!
string facename = "Arial"
string text = "REGLAS DEMOSTRATIVAS ~h97 NO CORRESPONDEN A UN PRODUCTO REAL DE SEGUROS"
alignment alignment = center!
long textcolor = 255
long backcolor = 67108864
end type

type st_datos from statictext within w_cotizador_mvp
integer x = 160
integer y = 330
integer width = 1200
integer height = 88
integer textsize = -11
integer weight = 700
fontcharset fontcharset = ansi!
fontfamily fontfamily = swiss!
fontpitch fontpitch = variable!
string facename = "Arial"
string text = "1. Datos de entrada"
long backcolor = 67108864
end type

type st_edad_etiqueta from statictext within w_cotizador_mvp
integer x = 200
integer y = 455
integer width = 420
integer height = 88
integer textsize = -10
integer weight = 400
fontcharset fontcharset = ansi!
fontfamily fontfamily = swiss!
fontpitch fontpitch = variable!
string facename = "Arial"
string text = "Edad:"
long backcolor = 67108864
end type

type sle_edad from singlelineedit within w_cotizador_mvp
integer x = 620
integer y = 440
integer width = 500
integer height = 110
integer taborder = 10
integer textsize = -10
integer weight = 400
fontcharset fontcharset = ansi!
fontfamily fontfamily = swiss!
fontpitch fontpitch = variable!
string facename = "Arial"
borderstyle borderstyle = stylelowered!
end type

type st_categoria_etiqueta from statictext within w_cotizador_mvp
integer x = 1280
integer y = 455
integer width = 650
integer height = 88
integer textsize = -10
integer weight = 400
fontcharset fontcharset = ansi!
fontfamily fontfamily = swiss!
fontpitch fontpitch = variable!
string facename = "Arial"
string text = "Categoria:"
long backcolor = 67108864
end type

type ddlb_categoria from dropdownlistbox within w_cotizador_mvp
integer x = 1900
integer y = 440
integer width = 850
integer height = 500
integer taborder = 20
integer textsize = -10
integer weight = 400
fontcharset fontcharset = ansi!
fontfamily fontfamily = swiss!
fontpitch fontpitch = variable!
string facename = "Arial"
boolean allowedit = false
boolean vscrollbar = true
end type

type st_descuento_etiqueta from statictext within w_cotizador_mvp
integer x = 2900
integer y = 455
integer width = 820
integer height = 88
integer textsize = -10
integer weight = 400
fontcharset fontcharset = ansi!
fontfamily fontfamily = swiss!
fontpitch fontpitch = variable!
string facename = "Arial"
string text = "Descuento (%):"
long backcolor = 67108864
end type

type sle_descuento from singlelineedit within w_cotizador_mvp
integer x = 3700
integer y = 440
integer width = 500
integer height = 110
integer taborder = 30
integer textsize = -10
integer weight = 400
fontcharset fontcharset = ansi!
fontfamily fontfamily = swiss!
fontpitch fontpitch = variable!
string facename = "Arial"
borderstyle borderstyle = stylelowered!
end type

type cb_calcular from commandbutton within w_cotizador_mvp
integer x = 4380
integer y = 430
integer width = 650
integer height = 130
integer taborder = 40
integer textsize = -10
integer weight = 700
fontcharset fontcharset = ansi!
fontfamily fontfamily = swiss!
fontpitch fontpitch = variable!
string facename = "Arial"
string text = "Calcular"
boolean default = true
end type

event clicked;
w_cotizador_mvp lw_ventana
lw_ventana = parent
lw_ventana.of_calcular()
end event

type cb_limpiar from commandbutton within w_cotizador_mvp
integer x = 5120
integer y = 430
integer width = 650
integer height = 130
integer taborder = 50
integer textsize = -10
integer weight = 400
fontcharset fontcharset = ansi!
fontfamily fontfamily = swiss!
fontpitch fontpitch = variable!
string facename = "Arial"
string text = "Limpiar"
end type

event clicked;
w_cotizador_mvp lw_ventana
lw_ventana = parent
lw_ventana.of_limpiar()
end event

type st_desglose from statictext within w_cotizador_mvp
integer x = 160
integer y = 690
integer width = 1600
integer height = 88
integer textsize = -11
integer weight = 700
fontcharset fontcharset = ansi!
fontfamily fontfamily = swiss!
fontpitch fontpitch = variable!
string facename = "Arial"
string text = "2. Resultado y desglose"
long backcolor = 67108864
end type

type st_prima_base_etiqueta from statictext within w_cotizador_mvp
integer x = 200
integer y = 830
integer width = 900
integer height = 78
string text = "Prima base:"
long backcolor = 67108864
end type

type st_prima_base_valor from statictext within w_cotizador_mvp
integer x = 1150
integer y = 830
integer width = 750
integer height = 78
string text = "-"
alignment alignment = right!
boolean border = true
long backcolor = 16777215
end type

type st_factor_edad_etiqueta from statictext within w_cotizador_mvp
integer x = 200
integer y = 955
integer width = 900
integer height = 78
string text = "Factor por edad:"
long backcolor = 67108864
end type

type st_factor_edad_valor from statictext within w_cotizador_mvp
integer x = 1150
integer y = 955
integer width = 750
integer height = 78
string text = "-"
alignment alignment = right!
boolean border = true
long backcolor = 16777215
end type

type st_factor_categoria_etiqueta from statictext within w_cotizador_mvp
integer x = 200
integer y = 1080
integer width = 900
integer height = 78
string text = "Factor por categoria:"
long backcolor = 67108864
end type

type st_factor_categoria_valor from statictext within w_cotizador_mvp
integer x = 1150
integer y = 1080
integer width = 750
integer height = 78
string text = "-"
alignment alignment = right!
boolean border = true
long backcolor = 16777215
end type

type st_antes_descuento_etiqueta from statictext within w_cotizador_mvp
integer x = 200
integer y = 1205
integer width = 900
integer height = 78
string text = "Antes de descuento:"
long backcolor = 67108864
end type

type st_antes_descuento_valor from statictext within w_cotizador_mvp
integer x = 1150
integer y = 1205
integer width = 750
integer height = 78
string text = "-"
alignment alignment = right!
boolean border = true
long backcolor = 16777215
end type

type st_descuento_valor_etiqueta from statictext within w_cotizador_mvp
integer x = 200
integer y = 1330
integer width = 900
integer height = 78
string text = "Valor descuento:"
long backcolor = 67108864
end type

type st_descuento_valor from statictext within w_cotizador_mvp
integer x = 1150
integer y = 1330
integer width = 750
integer height = 78
string text = "-"
alignment alignment = right!
boolean border = true
long backcolor = 16777215
end type

type st_subtotal_etiqueta from statictext within w_cotizador_mvp
integer x = 200
integer y = 1455
integer width = 900
integer height = 78
string text = "Subtotal:"
long backcolor = 67108864
end type

type st_subtotal_valor from statictext within w_cotizador_mvp
integer x = 1150
integer y = 1455
integer width = 750
integer height = 78
string text = "-"
alignment alignment = right!
boolean border = true
long backcolor = 16777215
end type

type st_impuesto_etiqueta from statictext within w_cotizador_mvp
integer x = 200
integer y = 1580
integer width = 900
integer height = 78
string text = "Impuesto (15%):"
long backcolor = 67108864
end type

type st_impuesto_valor from statictext within w_cotizador_mvp
integer x = 1150
integer y = 1580
integer width = 750
integer height = 78
string text = "-"
alignment alignment = right!
boolean border = true
long backcolor = 16777215
end type

type st_deducible_etiqueta from statictext within w_cotizador_mvp
integer x = 200
integer y = 1705
integer width = 900
integer height = 78
string text = "Deducible fijo:"
long backcolor = 67108864
end type

type st_deducible_valor from statictext within w_cotizador_mvp
integer x = 1150
integer y = 1705
integer width = 750
integer height = 78
string text = "-"
alignment alignment = right!
boolean border = true
long backcolor = 16777215
end type

type st_prima_anual_etiqueta from statictext within w_cotizador_mvp
integer x = 2200
integer y = 830
integer width = 1200
integer height = 90
integer textsize = -11
integer weight = 700
string text = "Prima anual final:"
long backcolor = 67108864
end type

type st_prima_anual from statictext within w_cotizador_mvp
integer x = 3500
integer y = 815
integer width = 2200
integer height = 110
integer textsize = -14
integer weight = 700
string text = "-"
alignment alignment = right!
boolean border = true
long textcolor = 32768
long backcolor = 16777215
end type

type st_cuota_mensual_etiqueta from statictext within w_cotizador_mvp
integer x = 2200
integer y = 970
integer width = 1200
integer height = 90
integer textsize = -11
integer weight = 700
string text = "Cuota mensual fija:"
long backcolor = 67108864
end type

type st_cuota_mensual from statictext within w_cotizador_mvp
integer x = 3500
integer y = 955
integer width = 2200
integer height = 110
integer textsize = -14
integer weight = 700
string text = "-"
alignment alignment = right!
boolean border = true
long textcolor = 32768
long backcolor = 16777215
end type

type st_estado_etiqueta from statictext within w_cotizador_mvp
integer x = 2200
integer y = 1110
integer width = 1200
integer height = 90
integer textsize = -11
integer weight = 700
string text = "Estado:"
long backcolor = 67108864
end type

type st_estado from statictext within w_cotizador_mvp
integer x = 3500
integer y = 1095
integer width = 2200
integer height = 110
integer textsize = -11
integer weight = 700
string text = "Sin calcular"
alignment alignment = center!
boolean border = true
long backcolor = 16777215
end type

type st_explicacion_etiqueta from statictext within w_cotizador_mvp
integer x = 2200
integer y = 1260
integer width = 1200
integer height = 80
string text = "Explicacion:"
long backcolor = 67108864
end type

type mle_explicacion from multilineedit within w_cotizador_mvp
integer x = 3500
integer y = 1240
integer width = 2200
integer height = 550
integer taborder = 60
integer textsize = -9
integer weight = 400
fontcharset fontcharset = ansi!
fontfamily fontfamily = swiss!
fontpitch fontpitch = variable!
string facename = "Arial"
boolean displayonly = true
boolean vscrollbar = true
borderstyle borderstyle = stylelowered!
end type

type st_tabla_titulo from statictext within w_cotizador_mvp
integer x = 160
integer y = 1940
integer width = 3500
integer height = 90
integer textsize = -11
integer weight = 700
fontcharset fontcharset = ansi!
fontfamily fontfamily = swiss!
fontpitch fontpitch = variable!
string facename = "Arial"
string text = "3. Tabla comparativa por rango de edad"
long backcolor = 67108864
end type

type dw_tabla_edades from datawindow within w_cotizador_mvp
integer x = 160
integer y = 2050
integer width = 5600
integer height = 1800
integer taborder = 70
string dataobject = "d_tabla_primas_edad"
borderstyle borderstyle = stylelowered!
boolean livescroll = true
boolean vscrollbar = true
boolean hscrollbar = true
end type

