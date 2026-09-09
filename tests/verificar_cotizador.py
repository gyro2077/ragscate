#!/usr/bin/env python3
"""Verificacion local del MVP. No sustituye la compilacion en PowerBuilder 9."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "pb-src"


def dinero(valor: Decimal) -> Decimal:
    return valor.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def factor_edad(edad: int) -> Decimal:
    if 18 <= edad <= 25:
        return Decimal("1.20")
    if 26 <= edad <= 35:
        return Decimal("1.10")
    if 36 <= edad <= 50:
        return Decimal("1.00")
    if 51 <= edad <= 65:
        return Decimal("1.15")
    if 66 <= edad <= 75:
        return Decimal("1.35")
    raise ValueError("edad no admitida")


def factor_categoria(categoria: str) -> Decimal:
    factores = {
        "bajo": Decimal("1.00"),
        "medio": Decimal("1.15"),
        "alto": Decimal("1.30"),
    }
    try:
        return factores[categoria.strip().lower()]
    except KeyError as error:
        raise ValueError("categoria no admitida") from error


def cotizar(edad: int, categoria: str, descuento: Decimal) -> dict[str, object]:
    if descuento < 0 or descuento > 10:
        raise ValueError("descuento no admitido")
    antes = dinero(Decimal("120.00") * factor_edad(edad) * factor_categoria(categoria))
    valor_descuento = dinero(antes * descuento / Decimal("100"))
    subtotal = dinero(antes - valor_descuento)
    impuesto = dinero(subtotal * Decimal("15.00") / Decimal("100"))
    anual = dinero(subtotal + impuesto)
    mensual = dinero(anual / Decimal("12"))
    motivos = []
    if edad >= 66:
        motivos.append("edad")
    if categoria.strip().lower() == "alto":
        motivos.append("categoria")
    return {
        "antes": antes,
        "descuento": valor_descuento,
        "subtotal": subtotal,
        "impuesto": impuesto,
        "anual": anual,
        "mensual": mensual,
        "estado": "Requiere autorizacion" if motivos else "Aprobado",
        "motivos": motivos,
    }


def verificar_casos() -> None:
    casos = [
        (30, "Bajo", "0", "132.00", "0.00", "132.00", "19.80", "151.80", "12.65", "Aprobado", []),
        (45, "Medio", "5", "138.00", "6.90", "131.10", "19.67", "150.77", "12.56", "Aprobado", []),
        (70, "Alto", "10", "210.60", "21.06", "189.54", "28.43", "217.97", "18.16", "Requiere autorizacion", ["edad", "categoria"]),
    ]
    for edad, categoria, descuento, antes, desc, subtotal, impuesto, anual, mensual, estado, motivos in casos:
        resultado = cotizar(edad, categoria, Decimal(descuento))
        assert resultado["antes"] == Decimal(antes)
        assert resultado["descuento"] == Decimal(desc)
        assert resultado["subtotal"] == Decimal(subtotal)
        assert resultado["impuesto"] == Decimal(impuesto)
        assert resultado["anual"] == Decimal(anual)
        assert resultado["mensual"] == Decimal(mensual)
        assert resultado["estado"] == estado
        assert resultado["motivos"] == motivos

    invalidos = [
        (17, "Bajo", Decimal("0")),
        (76, "Bajo", Decimal("0")),
        (30, "", Decimal("0")),
        (30, "Bajo", Decimal("-1")),
        (30, "Bajo", Decimal("11")),
    ]
    for parametros in invalidos:
        try:
            cotizar(*parametros)
        except ValueError:
            pass
        else:
            raise AssertionError(f"El caso invalido fue aceptado: {parametros}")


def verificar_parentesis_datawindow(texto: str) -> None:
    profundidad = 0
    en_cadena = False
    escapado = False
    for caracter in texto:
        if en_cadena:
            if escapado:
                escapado = False
            elif caracter == "~":
                escapado = True
            elif caracter == '"':
                en_cadena = False
            continue
        if caracter == '"':
            en_cadena = True
        elif caracter == "(":
            profundidad += 1
        elif caracter == ")":
            profundidad -= 1
            assert profundidad >= 0, "DataWindow tiene un parentesis de cierre extra"
    assert not en_cadena, "DataWindow tiene una cadena sin cerrar"
    assert profundidad == 0, "DataWindow tiene parentesis sin cerrar"


def verificar_fuentes() -> None:
    esperados = {
        "str_resultado_cotizacion.srs": ["global type str_resultado_cotizacion from structure", "prima_anual", "motivos_autorizacion"],
        "n_cotizador_reglas.sru": ["of_factor_edad", "of_factor_categoria", "of_calcular_cotizacion", "round("],
        "d_tabla_primas_edad.srd": ["release 9;", "name=rango_edad", "name=prima_anual", "name=cuota_mensual", "name=condicion"],
        "w_cotizador_mvp.srw": ["global type w_cotizador_mvp from window", "cb_calcular", "cb_limpiar", "dw_tabla_edades", "of_actualizar_tabla"],
        "cotizador_mvp.sra": ["global type cotizador_mvp from application", "open(w_cotizador_mvp)"],
    }
    for nombre, fragmentos in esperados.items():
        ruta = SRC / nombre
        assert ruta.is_file(), f"Falta {ruta}"
        texto = ruta.read_text(encoding="ascii")
        assert texto.startswith(f"$PBExportHeader${nombre}"), f"Cabecera incorrecta: {nombre}"
        for fragmento in fragmentos:
            assert fragmento.lower() in texto.lower(), f"Falta {fragmento!r} en {nombre}"
        assert not re.search(r"[^\x00-\x7f]", texto), f"{nombre} contiene caracteres fuera de ASCII"

    verificar_parentesis_datawindow((SRC / "d_tabla_primas_edad.srd").read_text(encoding="ascii"))

    ventana = (SRC / "w_cotizador_mvp.srw").read_text(encoding="ascii").lower()
    for validacion in [
        'if ls_edad = "" then',
        "if not isnumber(ls_edad) then",
        'if as_categoria = "" then',
        'if ls_descuento = "" then',
        "if not isnumber(ls_descuento) then",
        "if adc_descuento < 0 or adc_descuento > 10 then",
    ]:
        assert validacion in ventana, f"Falta validacion de interfaz: {validacion}"

    respaldo = ROOT / "backups" / "initial-powerbuilder-skeleton-20260908" / "cotizador_mvp.pbl"
    assert respaldo.is_file(), "Falta el respaldo inicial de cotizador_mvp.pbl"
    assert respaldo.stat().st_size > 0, "El respaldo inicial de la PBL esta vacio"


def main() -> None:
    verificar_fuentes()
    verificar_casos()
    print("OK: 5 fuentes PowerBuilder presentes y estructuralmente consistentes.")
    print("OK: respaldo inicial de la PBL presente e intacto en su ubicacion protegida.")
    print("OK: 3 casos validos y todas las rutas de validacion solicitadas comprobadas.")
    print("INFO: ejecucion y Full Build de PowerBuilder 9.0.3 registrados en VALIDACION-PB9.md.")


if __name__ == "__main__":
    main()
