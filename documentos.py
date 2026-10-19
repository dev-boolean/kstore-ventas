"""Documentos de identificación colombianos: validación y formato.

- CC  (cédula de ciudadanía): de 6 a 10 dígitos, sin ceros a la izquierda.
        Se muestra con puntos de miles: 1.045.678.912
- CE  (cédula de extranjería): de 6 a 7 dígitos.       Se muestra: 845.123
- NIT (empresas): 9 dígitos + dígito de verificación (DV) calculado
        con el algoritmo módulo 11 de la DIAN.        Se muestra: 900.123.456-8

En la base de datos se guarda la forma normalizada (solo dígitos; el NIT
como 900123456-8). Las mismas reglas están como restricciones CHECK en
sql/schema.sql, así que la base de datos también las hace cumplir.
"""
import re

# Pesos de la DIAN, aplicados de derecha a izquierda sobre los dígitos del NIT
PESOS_DIAN = [3, 7, 13, 17, 19, 23, 29, 37, 41, 43, 47, 53, 59, 67, 71]

LONGITUDES = {"CC": (6, 10), "CE": (6, 7)}


def digito_verificacion(nit):
    """Calcula el dígito de verificación (DV) de un NIT."""
    suma = sum(int(d) * PESOS_DIAN[i] for i, d in enumerate(reversed(nit)))
    residuo = suma % 11
    return residuo if residuo < 2 else 11 - residuo


def _miles(digitos):
    return f"{int(digitos):,}".replace(",", ".")


def normalizar(tipo_doc, texto):
    """Valida un documento escrito por el usuario y lo deja en la forma que se guarda.

    Acepta puntos, espacios y guiones (1.045.678.912, 900.123.456-8).
    Si el NIT se escribe sin DV (9 dígitos), el DV se calcula solo.
    Lanza ValueError con un mensaje claro si el documento no es válido.
    """
    if not texto:
        raise ValueError("El número de documento es obligatorio.")
    limpio = re.sub(r"[\s.]", "", texto)

    if tipo_doc == "NIT":
        m = re.fullmatch(r"(\d{9})(?:-?(\d))?", limpio)
        if not m:
            raise ValueError("NIT inválido: debe tener 9 dígitos y su dígito de verificación, "
                             "por ejemplo 900.123.456-8.")
        base, dv = m.group(1), m.group(2)
        if base[0] not in "89":
            raise ValueError("NIT inválido: el NIT de una empresa empieza por 8 o 9.")
        esperado = digito_verificacion(base)
        if dv is not None and int(dv) != esperado:
            raise ValueError(f"NIT inválido: el dígito de verificación de {_miles(base)} "
                             f"debe ser {esperado}, no {dv}.")
        return f"{base}-{esperado}"

    minimo, maximo = LONGITUDES[tipo_doc]
    nombre = "cédula de ciudadanía" if tipo_doc == "CC" else "cédula de extranjería"
    if not limpio.isdigit():
        raise ValueError(f"La {nombre} solo puede tener números.")
    if limpio.startswith("0"):
        raise ValueError(f"La {nombre} no puede empezar por 0.")
    if not minimo <= len(limpio) <= maximo:
        raise ValueError(f"La {nombre} debe tener entre {minimo} y {maximo} dígitos.")
    return limpio


def formatear(tipo_doc, documento):
    """Forma de mostrar el documento: 1.045.678.912 · 845.123 · 900.123.456-8."""
    if not documento:
        return documento
    if tipo_doc == "NIT":
        m = re.fullmatch(r"(\d+)-(\d)", documento)
        return f"{_miles(m.group(1))}-{m.group(2)}" if m else documento
    return _miles(documento) if documento.isdigit() else documento
