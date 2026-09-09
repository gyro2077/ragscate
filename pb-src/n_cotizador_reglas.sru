$PBExportHeader$n_cotizador_reglas.sru
$PBExportComments$Reglas demostrativas centralizadas del cotizador MVP
forward
global type n_cotizador_reglas from nonvisualobject
end type
end forward

global type n_cotizador_reglas from nonvisualobject
end type
global n_cotizador_reglas n_cotizador_reglas

type variables
// REGLAS DEMOSTRATIVAS. NO CORRESPONDEN A UN PRODUCTO REAL DE SEGUROS.
private decimal idc_prima_base = 120.00
private decimal idc_impuesto_porcentaje = 15.00
private decimal idc_deducible = 250.00
end variables

forward prototypes
public function decimal of_factor_edad (integer ai_edad)
public function decimal of_factor_categoria (string as_categoria)
public function str_resultado_cotizacion of_calcular_cotizacion (integer ai_edad, string as_categoria, decimal adc_descuento)
end prototypes

public function decimal of_factor_edad (integer ai_edad);
// Una salida negativa indica que la edad no esta admitida.
choose case ai_edad
	case 18 to 25
		return 1.20
	case 26 to 35
		return 1.10
	case 36 to 50
		return 1.00
	case 51 to 65
		return 1.15
	case 66 to 75
		return 1.35
	case else
		return -1.00
end choose
end function

public function decimal of_factor_categoria (string as_categoria);
string ls_categoria

ls_categoria = lower(trim(as_categoria))

choose case ls_categoria
	case "bajo"
		return 1.00
	case "medio"
		return 1.15
	case "alto"
		return 1.30
	case else
		return -1.00
end choose
end function

public function str_resultado_cotizacion of_calcular_cotizacion (integer ai_edad, string as_categoria, decimal adc_descuento);
str_resultado_cotizacion lstr_resultado
boolean lb_autoriza_edad
boolean lb_autoriza_categoria

// Estado inicial. La ventana valida tambien, pero este objeto protege las reglas.
lstr_resultado.es_valido = false
lstr_resultado.mensaje_error = ""
lstr_resultado.edad = ai_edad
lstr_resultado.categoria = trim(as_categoria)
lstr_resultado.porcentaje_descuento = adc_descuento
lstr_resultado.prima_base = idc_prima_base
lstr_resultado.deducible = idc_deducible

lstr_resultado.factor_edad = of_factor_edad(ai_edad)
if lstr_resultado.factor_edad < 0 then
	lstr_resultado.mensaje_error = "La edad admitida debe estar entre 18 y 75 anos."
	return lstr_resultado
end if

lstr_resultado.factor_categoria = of_factor_categoria(as_categoria)
if lstr_resultado.factor_categoria < 0 then
	lstr_resultado.mensaje_error = "Seleccione una categoria: Bajo, Medio o Alto."
	return lstr_resultado
end if

if adc_descuento < 0 or adc_descuento > 10 then
	lstr_resultado.mensaje_error = "El descuento debe estar entre 0 y 10 por ciento."
	return lstr_resultado
end if

// Criterio de redondeo: cada importe monetario se redondea a dos decimales
// inmediatamente despues de calcularlo. La cuota usa la prima anual ya redondeada.
lstr_resultado.prima_antes_descuento = round(idc_prima_base * &
	lstr_resultado.factor_edad * lstr_resultado.factor_categoria, 2)
lstr_resultado.valor_descuento = round(lstr_resultado.prima_antes_descuento * &
	adc_descuento / 100, 2)
lstr_resultado.subtotal = round(lstr_resultado.prima_antes_descuento - &
	lstr_resultado.valor_descuento, 2)
lstr_resultado.impuesto = round(lstr_resultado.subtotal * &
	idc_impuesto_porcentaje / 100, 2)
lstr_resultado.prima_anual = round(lstr_resultado.subtotal + &
	lstr_resultado.impuesto, 2)
lstr_resultado.cuota_mensual = round(lstr_resultado.prima_anual / 12, 2)

lb_autoriza_edad = (ai_edad >= 66)
lb_autoriza_categoria = (lower(trim(as_categoria)) = "alto")

if lb_autoriza_edad or lb_autoriza_categoria then
	lstr_resultado.estado = "Requiere autorizacion"
	if lb_autoriza_edad and lb_autoriza_categoria then
		lstr_resultado.motivos_autorizacion = "Edad entre 66 y 75 anos y categoria Alto."
	elseif lb_autoriza_edad then
		lstr_resultado.motivos_autorizacion = "Edad entre 66 y 75 anos."
	else
		lstr_resultado.motivos_autorizacion = "Categoria Alto."
	end if
else
	lstr_resultado.estado = "Aprobado"
	lstr_resultado.motivos_autorizacion = "No aplica."
end if

lstr_resultado.explicacion = "USD " + &
	string(lstr_resultado.prima_base, "#,##0.00") + " x factor edad " + &
	string(lstr_resultado.factor_edad, "0.00") + " x factor categoria " + &
	string(lstr_resultado.factor_categoria, "0.00") + &
	"; descuento " + string(adc_descuento, "0.00") + &
	"%; impuesto " + string(idc_impuesto_porcentaje, "0.00") + "%. " + &
	"Estado: " + lstr_resultado.estado + ". Motivo: " + &
	lstr_resultado.motivos_autorizacion

lstr_resultado.es_valido = true
return lstr_resultado
end function

on n_cotizador_reglas.create
call super::create
TriggerEvent(this, "constructor")
end on

on n_cotizador_reglas.destroy
TriggerEvent(this, "destructor")
call super::destroy
end on

