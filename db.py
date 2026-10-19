"""Capa de acceso a datos: SQLite + registro de cada sentencia ejecutada.

Toda la aplicación pasa por la clase Database, que abre una conexión por
operación, activa las claves foráneas, registra el SQL en una bitácora
(el panel "Mensajes" de la interfaz) y traduce los errores de integridad
a mensajes en español.
"""
import re
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from documentos import formatear

BASE_DIR = Path(__file__).resolve().parent
SQL_DIR = BASE_DIR / "sql"
DB_PATH = BASE_DIR / "data" / "kstore.db"

MAX_LOG = 200


class DBError(Exception):
    """Error de base de datos con un mensaje entendible para el usuario."""


class Resultado:
    """Filas de un SELECT con los nombres de sus columnas."""

    def __init__(self, columnas, filas):
        self.columnas = columnas
        self.filas = filas

    def __len__(self):
        return len(self.filas)

    def __iter__(self):
        return (dict(zip(self.columnas, f)) for f in self.filas)


def _connect():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    # SQLite trae las claves foráneas desactivadas por defecto
    conn.execute("PRAGMA foreign_keys = ON")
    # Función SQL propia: formato_doc('CC', '1045678912') -> '1.045.678.912'
    conn.create_function("formato_doc", 2, formatear)
    return conn


def init_db(reset=False):
    """Crea las tablas y carga los datos de ejemplo si la BD no existe."""
    conn = _connect()
    try:
        existe = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'detalle_pedido'"
        ).fetchone()
        if reset or not existe:
            conn.executescript((SQL_DIR / "schema.sql").read_text(encoding="utf-8"))
            conn.executescript((SQL_DIR / "seed.sql").read_text(encoding="utf-8"))
            conn.commit()
    finally:
        conn.close()


def traducir_error(e):
    """Convierte los mensajes de SQLite en mensajes claros en español."""
    msg = str(e)
    if "UNIQUE constraint failed" in msg:
        campo = msg.split(":", 1)[1].strip()
        return f"Valor duplicado: ya existe un registro con el mismo {campo} (restricción UNIQUE / PRIMARY KEY)."
    if "FOREIGN KEY constraint failed" in msg:
        return ("Integridad referencial: el registro está relacionado con otros datos "
                "o hace referencia a uno que no existe (FOREIGN KEY).")
    if "CHECK constraint failed" in msg:
        regla = msg.split(":", 1)[1].strip()
        return f"Dato no válido: se incumple la restricción CHECK '{regla}'."
    if "NOT NULL constraint failed" in msg:
        campo = msg.split(":", 1)[1].strip()
        return f"Campo obligatorio vacío: {campo} (NOT NULL)."
    return msg


def _formatear_sql(sql, params):
    """Arma la sentencia con los parámetros incrustados, solo para mostrarla."""
    texto = re.sub(r"\s+", " ", sql).strip()
    for p in params:
        if p is None:
            valor = "NULL"
        elif isinstance(p, str):
            valor = "'" + p.replace("'", "''") + "'"
        else:
            valor = str(p)
        texto = texto.replace("?", valor, 1)
    return texto


def _quitar_comentarios_iniciales(sentencia):
    lineas = sentencia.strip().splitlines()
    while lineas and (not lineas[0].strip() or lineas[0].strip().startswith("--")):
        lineas.pop(0)
    return "\n".join(lineas).strip()


def dividir_sentencias(script):
    """Separa un script en sentencias completas (respeta triggers y cadenas)."""
    sentencias, actual = [], ""
    for trozo in script.split(";"):
        actual += trozo + ";"
        if sqlite3.complete_statement(actual):
            sentencias.append(actual)
            actual = ""
    sentencias.append(actual)
    limpias = (_quitar_comentarios_iniciales(s) for s in sentencias)
    return [s for s in limpias if s.strip(" \t\r\n;")]


class Database:
    def __init__(self, log):
        # log es la bitácora de la sesión del usuario (lista de tuplas)
        self.log = log

    # ------------------------------------------------------------ bitácora
    def _registrar(self, estado, texto):
        if self.log and self.log[-1][1:] == (estado, texto):
            return  # no repetir la misma línea seguida
        self.log.append((datetime.now().strftime("%H:%M:%S"), estado, texto))
        del self.log[:-MAX_LOG]

    def _ejecutar(self, conn, sql, params=()):
        params = tuple(params)
        try:
            cur = conn.execute(sql, params)
        except sqlite3.Error as e:
            self._registrar("ERR", _formatear_sql(sql, params) + "  -->  " + str(e))
            raise
        detalle = ""
        if cur.description is None and cur.rowcount >= 0:
            detalle = f"  ({cur.rowcount} fila(s))"
        self._registrar("OK", _formatear_sql(sql, params) + detalle)
        return cur

    # ------------------------------------------------------------ lectura
    def consultar(self, sql, params=(), registrar=True):
        """SELECT que devuelve un Resultado (columnas + filas)."""
        conn = _connect()
        try:
            cur = self._ejecutar(conn, sql, params) if registrar else conn.execute(sql, tuple(params))
            return Resultado([c[0] for c in cur.description], cur.fetchall())
        except sqlite3.Error as e:
            raise DBError(traducir_error(e)) from e
        finally:
            conn.close()

    def valor(self, sql, params=()):
        """Primer valor de un SELECT (sin registrar en la bitácora)."""
        conn = _connect()
        try:
            fila = conn.execute(sql, tuple(params)).fetchone()
            return fila[0] if fila else None
        finally:
            conn.close()

    def fila(self, sql, params=()):
        """Primera fila de un SELECT como diccionario (sin registrar)."""
        conn = _connect()
        conn.row_factory = sqlite3.Row
        try:
            fila = conn.execute(sql, tuple(params)).fetchone()
            return dict(fila) if fila else None
        finally:
            conn.close()

    # ------------------------------------------------------------ escritura
    def ejecutar(self, sql, params=()):
        """INSERT / UPDATE / DELETE individual. Devuelve el id insertado."""
        with self.transaccion() as run:
            return run(sql, params).lastrowid

    @contextmanager
    def transaccion(self):
        """Agrupa varias sentencias: o se guardan todas o ninguna.

        Uso:
            with db.transaccion() as run:
                run("INSERT ...", (...))
                run("UPDATE ...", (...))
        """
        conn = _connect()
        self._registrar("TX", "BEGIN TRANSACTION")
        try:
            yield lambda sql, params=(): self._ejecutar(conn, sql, params)
            conn.commit()
            self._registrar("TX", "COMMIT")
        except sqlite3.Error as e:
            conn.rollback()
            self._registrar("TX", "ROLLBACK")
            raise DBError(traducir_error(e)) from e
        except Exception:
            conn.rollback()
            self._registrar("TX", "ROLLBACK")
            raise
        finally:
            conn.close()

    def ejecutar_script(self, script):
        """Consola SQL: ejecuta varias sentencias en una sola transacción.

        Devuelve una lista de (sentencia, Resultado o None, filas afectadas).
        """
        resultados = []
        with self.transaccion() as run:
            for s in dividir_sentencias(script):
                cur = run(s)
                if cur.description is not None:
                    res = Resultado([c[0] for c in cur.description], cur.fetchall())
                    resultados.append((s, res, len(res)))
                else:
                    resultados.append((s, None, cur.rowcount))
        return resultados

    def reiniciar(self):
        init_db(reset=True)
        self._registrar("TX", "Base de datos recreada (schema.sql + seed.sql)")


def cargar_consultas():
    """Lee sql/consultas.sql y devuelve la lista de consultas."""
    texto = (SQL_DIR / "consultas.sql").read_text(encoding="utf-8")
    bloques = re.split(r"^-- @ (.+)$", texto, flags=re.MULTILINE)
    consultas = []
    # bloques = [cabecera, titulo1, cuerpo1, titulo2, cuerpo2, ...]
    for titulo, cuerpo in zip(bloques[1::2], bloques[2::2]):
        descripcion, sql = [], []
        for linea in cuerpo.strip().splitlines():
            if linea.startswith("--") and not sql:
                descripcion.append(linea[2:].strip())
            else:
                sql.append(linea)
        consultas.append({
            "titulo": titulo.strip(),
            "descripcion": " ".join(descripcion),
            "sql": "\n".join(sql).strip(),
        })
    return consultas
