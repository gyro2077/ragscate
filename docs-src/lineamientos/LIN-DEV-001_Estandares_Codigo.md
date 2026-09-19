# LIN-DEV-001 — Estándares de Código para Sistemas Legacy

## 1. Nomenclatura

### 1.1 Prefijos obligatorios

| Prefijo | Uso | Ejemplo |
|---|---|---|
| of_ | Funciones y subrutinas públicas | of_calcular_cotizacion |
| idc_ | Constantes de instancia (Decimal) | idc_prima_base |
| ldc_ | Variables locales (Decimal) | ldc_subtotal |
| ai_ | Argumentos de entrada (Integer) | ai_edad |
| as_ | Argumentos de entrada (String) | as_categoria |
| adc_ | Argumentos de entrada (Decimal) | adc_descuento |
| cb_ | Botones (CommandButton) | cb_calcular |
| ddlb_ | Listas desplegables (DropDownListBox) | ddlb_categoria |
| sle_ | Campos de texto (SingleLineEdit) | sle_edad |
| lb_ | Variables locales booleanas | lb_autoriza_edad |
| ls_ | Variables locales string | ls_categoria |
| lstr_ | Variables locales estructura | lstr_resultado |
| str_ | Estructuras globales | str_resultado_cotizacion |
| n_ | Non-Visual Objects | n_cotizador_reglas |
| w_ | Windows | w_cotizador_mvp |
| d_ | DataWindows | d_tabla_primas_edad |

### 1.2 Nombres descriptivos

Los nombres deben describir la función, no abreviar.
Correcto: of_calcular_cotizacion. Incorrecto: of_calc_cot.

## 2. Variables y Constantes

### 2.1 Constantes configurables

Toda constante que pueda cambiar por decisión de negocio (porcentajes, montos base)
debe declararse como variable de instancia privada en el objeto de reglas,
no como valor literal en el código.

Correcto:
    private decimal idc_impuesto_porcentaje = 15.00
    lstr_resultado.impuesto = round(lstr_resultado.subtotal * idc_impuesto_porcentaje / 100, 2)

Incorrecto:
    lstr_resultado.impuesto = round(lstr_resultado.subtotal * 15.00 / 100, 2)

## 3. Funciones y Subrutinas

### 3.1 Responsabilidad única

Cada función debe hacer una sola cosa. Si una función supera 50 líneas,
considerar dividirla.

### 3.2 Validación defensiva

Aunque la ventana valide las entradas, el objeto de reglas debe validar
independientemente para proteger la integridad del cálculo.

### 3.3 Retorno de error

Para funciones que retornan factores, usar -1.00 como indicador de rechazo.
El código llamante debe verificar este valor antes de continuar.

### 3.4 Redondeo monetario

Todos los cálculos monetarios deben usar Round(valor, 2) inmediatamente
después de cada operación aritmética.

## 4. Aprobación

Aprobado por: Patricio Argüello — Arquitecto de Software
Fecha de aprobación: 2024-06-10
Versión: 1.0
