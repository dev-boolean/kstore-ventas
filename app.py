"""KStore S.A.S. - Sistema de Pedidos (Laboratorio 01 - Bases de Datos).

Aplicación web en Flask con interfaz estilo terminal (ncurses / menuconfig)
sobre una base de datos relacional SQLite.

Ejecutar en el computador:   python app.py      -> http://localhost:5000
En el servidor (Render):     gunicorn app:app
"""
import os
import sqlite3
import uuid
from datetime import date, datetime

from flask import (Flask, abort, flash, redirect, render_template, request,
                   send_file, session, url_for)

from db import (DB_PATH, SQL_DIR, Database, DBError, cargar_consultas,
                init_db)
from documentos import formatear, normalizar

# ---------------------------------------------------------------- datos fijos
EMPRESA = "KStore S.A.S."
NIT_EMPRESA = "901.555.777-4"
VERSION = "2.0"
CURSO = "Laboratorio 01 - Bases de Datos"
INTEGRANTES = [
    "Andrés Parejo",
    "Valeria Flórez",
    "Víctor Mendoza",
    "Santiago Molina",
    "Sara Ibáñez",
]
COLUMNAS_DINERO = {"precio_unitario", "precio_compra", "subtotal", "total", "total_comprado"}

MENU = [
    ("1", "inicio", "Inicio / Status"),
    ("2", "clientes", "Clientes  --->"),
    ("3", "productos", "Productos  --->"),
    ("4", "proveedores", "Proveedores  --->"),
    ("5", "pedidos", "Pedidos  --->"),
    ("6", "consultas", "Consultas  --->"),
    ("7", "consola", "Consola SQL"),
    ("8", "modelo", "Modelo E-R  --->"),
    ("0", "sistema", "Sistema"),
]

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "kstore-laboratorio-01")
init_db()

# Bitácora SQL de cada visitante (se guarda en memoria del servidor)
BITACORAS = {}


def bd():
    """Base de datos con la bitácora de la sesión actual."""
    if "sid" not in session:
        session["sid"] = uuid.uuid4().hex
    return Database(BITACORAS.setdefault(session["sid"], []))


# ---------------------------------------------------------------- filtros
@app.template_filter("dinero")
def dinero(v):
    return "$ " + f"{(v or 0):,.0f}".replace(",", ".")


@app.template_filter("celda")
def celda(valor, columna):
    if valor is None:
        return ""
    if columna in COLUMNAS_DINERO:
        return dinero(valor)
    return valor


@app.context_processor
def contexto():
    sid = session.get("sid")
    return {
        "EMPRESA": EMPRESA, "VERSION": VERSION, "CURSO": CURSO, "MENU": MENU,
        "ahora": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "bitacora": list(reversed(BITACORAS.get(sid, [])[-60:])),
        "sqlite_version": sqlite3.sqlite_version,
        "COLUMNAS_DINERO": COLUMNAS_DINERO,
    }


# ---------------------------------------------------------------- CRUD genérico
def validar_cliente(v):
    v["identificacion"] = normalizar(v["tipo_doc"], v["identificacion"])
    if v["fecha_nacimiento"] and v["fecha_nacimiento"] > date.today().isoformat():
        raise ValueError("La fecha de nacimiento no puede ser futura.")


def validar_proveedor(v):
    v["nit"] = normalizar("NIT", v["nit"])


def validar_producto(v):
    if v["codigo"]:
        v["codigo"] = v["codigo"].upper()


ENTIDADES = {
    "clientes": {
        "titulo": "Clientes", "singular": "Cliente", "tabla": "cliente", "pk": "id_cliente",
        "listar": """SELECT id_cliente AS id, tipo_doc,
                            formato_doc(tipo_doc, identificacion) AS identificacion,
                            nombre, apellidos, direccion, fecha_nacimiento,
                            CAST((julianday('now') - julianday(fecha_nacimiento)) / 365.25 AS INTEGER) AS edad
                       FROM cliente""",
        "orden": "apellidos, nombre",
        "buscar": ["identificacion", "nombre", "apellidos", "direccion"],
        "etiqueta": "formato_doc(tipo_doc, identificacion) || '  ' || nombre || ' ' || apellidos",
        "validar": validar_cliente,
        "campos": [
            {"col": "tipo_doc", "label": "Tipo de documento", "tipo": "select",
             "opciones": [("CC", "CC - Cédula de ciudadanía"), ("CE", "CE - Cédula de extranjería")]},
            {"col": "identificacion", "label": "Identificación", "placeholder": "1.045.678.912",
             "mostrar": lambda f: formatear(f.get("tipo_doc"), f.get("identificacion"))},
            {"col": "nombre", "label": "Nombre"},
            {"col": "apellidos", "label": "Apellidos"},
            {"col": "direccion", "label": "Dirección", "placeholder": "Calle 84 # 45-20, Barranquilla"},
            {"col": "fecha_nacimiento", "label": "Fecha de nacimiento", "tipo": "fecha"},
        ],
    },
    "productos": {
        "titulo": "Productos", "singular": "Producto", "tabla": "producto", "pk": "id_producto",
        "listar": """SELECT p.id_producto AS id, p.codigo, p.nombre, p.precio_unitario,
                            pv.nombre AS proveedor
                       FROM producto p JOIN proveedor pv ON pv.id_proveedor = p.id_proveedor""",
        "orden": "codigo",
        "buscar": ["codigo", "nombre", "proveedor"],
        "etiqueta": "codigo || '  ' || nombre",
        "validar": validar_producto,
        "campos": [
            {"col": "codigo", "label": "Código", "placeholder": "PER-005"},
            {"col": "nombre", "label": "Nombre"},
            {"col": "precio_unitario", "label": "Precio unitario ($)", "tipo": "numero"},
            {"col": "id_proveedor", "label": "Proveedor", "tipo": "fk",
             "sql": "SELECT id_proveedor, nombre FROM proveedor ORDER BY nombre"},
        ],
    },
    "proveedores": {
        "titulo": "Proveedores", "singular": "Proveedor", "tabla": "proveedor", "pk": "id_proveedor",
        "listar": """SELECT pv.id_proveedor AS id, formato_doc('NIT', pv.nit) AS nit, pv.nombre,
                            pv.direccion, COUNT(p.id_producto) AS productos
                       FROM proveedor pv LEFT JOIN producto p ON p.id_proveedor = pv.id_proveedor
                      GROUP BY pv.id_proveedor""",
        "orden": "nombre",
        "buscar": ["nit", "nombre", "direccion"],
        "etiqueta": "formato_doc('NIT', nit) || '  ' || nombre",
        "validar": validar_proveedor,
        "campos": [
            {"col": "nit", "label": "NIT", "placeholder": "900.123.456-8 (el DV se calcula si se omite)",
             "mostrar": lambda f: formatear("NIT", f.get("nit"))},
            {"col": "nombre", "label": "Nombre"},
            {"col": "direccion", "label": "Dirección"},
        ],
    },
}


def entidad(nombre):
    if nombre not in ENTIDADES:
        abort(404)
    return ENTIDADES[nombre]


def opciones_fk(campo):
    return bd().consultar(campo["sql"], registrar=False).filas


def leer_formulario(cfg):
    """Toma los campos del formulario; un texto vacío se guarda como NULL (NOT NULL actúa)."""
    valores = {}
    for c in cfg["campos"]:
        valor = request.form.get(c["col"], "").strip()
        valores[c["col"]] = valor or None
    return valores


def valores_para_mostrar(cfg, fila):
    return {c["col"]: (c["mostrar"](fila) if "mostrar" in c else fila.get(c["col"])) for c in cfg["campos"]}


@app.route("/<nombre>")
def listar(nombre):
    if nombre in ("favicon.ico",):
        abort(404)
    cfg = entidad(nombre)
    texto = request.args.get("q", "").strip()
    sql = f"SELECT * FROM ({cfg['listar']}) AS t"
    params = []
    if texto:
        # Se ignoran los puntos para encontrar 1045678912 aunque se muestre 1.045.678.912
        sql += " WHERE " + " OR ".join(f"REPLACE({c}, '.', '') LIKE ?" for c in cfg["buscar"])
        params = [f"%{texto.replace('.', '')}%"] * len(cfg["buscar"])
    sql += f" ORDER BY {cfg['orden']}"
    return render_template("lista.html", menu=nombre, cfg=cfg, nombre=nombre, q=texto,
                           res=bd().consultar(sql, params))


@app.route("/<nombre>/nuevo", methods=["GET", "POST"])
def nuevo(nombre):
    cfg = entidad(nombre)
    valores = {}
    if request.method == "POST":
        valores = leer_formulario(cfg)
        try:
            cfg["validar"](valores)
            columnas = list(valores)
            bd().ejecutar(f"INSERT INTO {cfg['tabla']} ({', '.join(columnas)}) "
                          f"VALUES ({', '.join('?' * len(columnas))})", list(valores.values()))
        except (ValueError, DBError) as e:
            flash(str(e), "err")
        else:
            flash(f"{cfg['singular']} registrado correctamente.", "ok")
            return redirect(url_for("listar", nombre=nombre))
    return render_template("form.html", menu=nombre, cfg=cfg, nombre=nombre, valores=valores,
                           accion="Nuevo", opciones_fk=opciones_fk)


@app.route("/<nombre>/<int:id>/editar", methods=["GET", "POST"])
def editar(nombre, id):
    cfg = entidad(nombre)
    fila = bd().fila(f"SELECT * FROM {cfg['tabla']} WHERE {cfg['pk']} = ?", (id,))
    if not fila:
        abort(404)
    valores = valores_para_mostrar(cfg, fila)
    if request.method == "POST":
        valores = leer_formulario(cfg)
        try:
            cfg["validar"](valores)
            asignaciones = ", ".join(f"{c} = ?" for c in valores)
            bd().ejecutar(f"UPDATE {cfg['tabla']} SET {asignaciones} WHERE {cfg['pk']} = ?",
                          list(valores.values()) + [id])
        except (ValueError, DBError) as e:
            flash(str(e), "err")
        else:
            flash(f"{cfg['singular']} #{id} actualizado.", "ok")
            return redirect(url_for("listar", nombre=nombre))
    return render_template("form.html", menu=nombre, cfg=cfg, nombre=nombre, valores=valores,
                           accion=f"Editar #{id}", opciones_fk=opciones_fk)


@app.route("/<nombre>/<int:id>/eliminar", methods=["GET", "POST"])
def eliminar(nombre, id):
    cfg = entidad(nombre)
    fila = bd().fila(f"SELECT * FROM {cfg['tabla']} WHERE {cfg['pk']} = ?", (id,))
    if not fila:
        abort(404)
    if request.method == "POST":
        try:
            bd().ejecutar(f"DELETE FROM {cfg['tabla']} WHERE {cfg['pk']} = ?", (id,))
        except DBError as e:
            flash(str(e), "err")
        else:
            flash(f"{cfg['singular']} #{id} eliminado.", "ok")
            return redirect(url_for("listar", nombre=nombre))
    return render_template("eliminar.html", menu=nombre, cfg=cfg, nombre=nombre, fila=fila, id=id)


# ---------------------------------------------------------------- inicio
LETRAS_BANNER = {
    "K": [" _  __", "| |/ /", "| ' < ", "|_|\\_\\", "      "],
    "S": ["  ___ ", " / __|", " \\__ \\", " |___/", "      "],
    "t": [" _   ", "| |_ ", "|  _|", " \\__|", "     "],
    "o": ["     ", " ___ ", "/ _ \\", "\\___/", "     "],
    "r": ["     ", " _ _ ", "| '_|", "|_|  ", "     "],
    "e": ["     ", " ___ ", "/ -_)", "\\___|", "     "],
}


def banner(texto):
    return "\n".join("".join(LETRAS_BANNER[c][i] for c in texto) for i in range(4))


@app.route("/")
@app.route("/inicio")
def inicio():
    d = bd()
    estado = [
        ("Base de datos:", f"SQLite {sqlite3.sqlite_version} ({DB_PATH.name})"),
        ("Clientes:", d.valor("SELECT COUNT(*) FROM cliente")),
        ("Productos:", d.valor("SELECT COUNT(*) FROM producto")),
        ("Proveedores:", d.valor("SELECT COUNT(*) FROM proveedor")),
        ("Pedidos:", d.valor("SELECT COUNT(*) FROM pedido")),
        ("Total vendido:", dinero(d.valor("SELECT COALESCE(SUM(total), 0) FROM v_pedido_resumen"))),
        ("Clientes sin pedidos:", d.valor("SELECT COUNT(*) FROM cliente c WHERE NOT EXISTS "
                                          "(SELECT 1 FROM pedido p WHERE p.id_cliente = c.id_cliente)")),
    ]
    ultimos = d.consultar("SELECT id_pedido AS pedido, fecha, cliente, unidades, total "
                          "FROM v_pedido_resumen ORDER BY fecha DESC LIMIT 6", registrar=False)
    return render_template("inicio.html", menu="inicio", banner=banner("KStore"), estado=estado,
                           ultimos=ultimos, integrantes=INTEGRANTES, nit=NIT_EMPRESA)


# ---------------------------------------------------------------- pedidos
@app.route("/pedidos")
def pedidos():
    texto = request.args.get("q", "").strip()
    sql = "SELECT id_pedido AS pedido, fecha, cliente, productos, unidades, total FROM v_pedido_resumen"
    params = []
    if texto:
        sql += " WHERE cliente LIKE ?"
        params = [f"%{texto}%"]
    sql += " ORDER BY fecha DESC"
    return render_template("pedidos.html", menu="pedidos", res=bd().consultar(sql, params), q=texto)


def carrito():
    return session.setdefault("carrito", [])


@app.route("/pedidos/nuevo", methods=["GET", "POST"])
def pedido_nuevo():
    d = bd()
    productos = {f[0]: f for f in d.consultar(
        "SELECT p.id_producto, p.codigo, p.nombre, p.precio_unitario, pv.nombre "
        "FROM producto p JOIN proveedor pv ON pv.id_proveedor = p.id_proveedor ORDER BY p.codigo",
        registrar=False).filas}
    clientes = d.consultar("SELECT id_cliente, formato_doc(tipo_doc, identificacion) || '  ' || "
                           "nombre || ' ' || apellidos FROM cliente ORDER BY apellidos", registrar=False).filas
    items = carrito()

    if request.method == "POST":
        accion = request.form.get("accion")
        if "id_cliente" in request.form:
            session["pedido_cliente"] = request.form.get("id_cliente", type=int)
        if accion == "agregar":
            pid = request.form.get("id_producto", type=int)
            cantidad = request.form.get("cantidad", type=int) or 0
            if pid not in productos or cantidad < 1:
                flash("Elija un producto y una cantidad mayor que cero.", "warn")
            else:
                existente = next((it for it in items if it["id_producto"] == pid), None)
                if existente:
                    existente["cantidad"] += cantidad
                else:
                    items.append({"id_producto": pid, "cantidad": cantidad})
        elif accion == "quitar":
            i = request.form.get("indice", type=int)
            if i is not None and 0 <= i < len(items):
                items.pop(i)
        elif accion == "vaciar":
            items.clear()
        elif accion == "confirmar":
            id_cliente = session.get("pedido_cliente")
            if not items or not id_cliente:
                flash("Elija el cliente y agregue al menos un producto.", "warn")
            else:
                try:
                    # Pedido + detalle en una sola transacción: o se guarda todo o nada
                    with d.transaccion() as run:
                        id_pedido = run("INSERT INTO pedido (id_cliente) VALUES (?)", (id_cliente,)).lastrowid
                        for it in items:
                            run("INSERT INTO detalle_pedido (id_pedido, id_producto, cantidad, precio_compra) "
                                "VALUES (?, ?, ?, ?)",
                                (id_pedido, it["id_producto"], it["cantidad"], productos[it["id_producto"]][3]))
                except DBError as e:
                    flash(f"El pedido no se registró (ROLLBACK): {e}", "err")
                else:
                    items.clear()
                    session.modified = True
                    flash(f"Pedido #{id_pedido:05d} registrado.", "ok")
                    return redirect(url_for("pedido_detalle", id=id_pedido))
        session.modified = True
        return redirect(url_for("pedido_nuevo"))

    lineas = []
    for i, it in enumerate(items):
        p = productos.get(it["id_producto"])
        if p:
            lineas.append({"indice": i, "codigo": p[1], "producto": p[2], "proveedor": p[4],
                           "cantidad": it["cantidad"], "precio": p[3], "valor": p[3] * it["cantidad"]})
    return render_template("pedido_nuevo.html", menu="pedidos", productos=productos.values(),
                           clientes=clientes, lineas=lineas, total=sum(l["valor"] for l in lineas),
                           cliente_actual=session.get("pedido_cliente"))


def factura_texto(id_pedido):
    d = bd()
    p = d.fila("SELECT r.*, c.tipo_doc, c.identificacion, c.direccion FROM v_pedido_resumen r "
               "JOIN cliente c ON c.id_cliente = r.id_cliente WHERE r.id_pedido = ?", (id_pedido,))
    if not p:
        abort(404)
    items = d.consultar("SELECT pr.codigo, pr.nombre, d.cantidad, d.precio_compra, pv.nombre AS proveedor "
                        "FROM detalle_pedido d JOIN producto pr ON pr.id_producto = d.id_producto "
                        "JOIN proveedor pv ON pv.id_proveedor = pr.id_proveedor "
                        "WHERE d.id_pedido = ? ORDER BY pr.codigo", (id_pedido,), registrar=False)
    w = 84
    interior = w - 4

    def fila(izq, der=""):
        izq = izq[: interior - len(der) - 1] if der else izq[:interior]
        return "│ " + izq + " " * (interior - len(izq) - len(der)) + der + " │"

    sep = "├" + "─" * (w - 2) + "┤"
    lineas = [
        "┌" + "─" * (w - 2) + "┐",
        fila(EMPRESA.upper(), f"NIT {NIT_EMPRESA}"),
        fila("Barranquilla, Atlántico", f"PEDIDO No. {id_pedido:05d}"),
        sep,
        fila(f"Cliente   : {p['cliente']}", f"{p['tipo_doc']} {formatear(p['tipo_doc'], p['identificacion'])}"),
        fila(f"Dirección : {p['direccion']}"),
        fila(f"Fecha     : {p['fecha']}"),
        sep,
        fila(f"{'CÓDIGO':<8} {'PRODUCTO':<26} {'PROVEEDOR':<14} {'CANT':>4} {'PRECIO':>11} {'VALOR':>11}"),
        sep,
    ]
    for it in items:
        lineas.append(fila(f"{it['codigo']:<8} {it['nombre'][:26]:<26} {it['proveedor'][:14]:<14} "
                           f"{it['cantidad']:>4} {dinero(it['precio_compra']):>11} "
                           f"{dinero(it['cantidad'] * it['precio_compra']):>11}"))
    lineas += [sep, fila("", f"TOTAL {dinero(p['total']):>16}"), "└" + "─" * (w - 2) + "┘"]
    return "\n".join(lineas)


@app.route("/pedidos/<int:id>")
def pedido_detalle(id):
    return render_template("pedido_detalle.html", menu="pedidos", id=id, factura=factura_texto(id))


@app.route("/pedidos/<int:id>/eliminar", methods=["POST"])
def pedido_eliminar(id):
    try:
        bd().ejecutar("DELETE FROM pedido WHERE id_pedido = ?", (id,))
    except DBError as e:
        flash(str(e), "err")
        return redirect(url_for("pedido_detalle", id=id))
    flash(f"Pedido #{id:05d} eliminado (su detalle se borró en cascada).", "ok")
    return redirect(url_for("pedidos"))


# ---------------------------------------------------------------- consultas
@app.route("/consultas")
def consultas():
    lista = cargar_consultas()
    n = min(max(request.args.get("n", 1, type=int), 1), len(lista))
    actual = lista[n - 1]
    try:
        res, error = bd().consultar(actual["sql"]), None
    except DBError as e:
        res, error = None, str(e)
    return render_template("consultas.html", menu="consultas", lista=lista, n=n, actual=actual,
                           res=res, error=error)


# ---------------------------------------------------------------- consola SQL
EJEMPLOS_SQL = {
    "Listar tablas": "SELECT name, type FROM sqlite_master WHERE type IN ('table', 'view') ORDER BY name;",
    "Pedidos con su cliente (JOIN)": (
        "SELECT pe.id_pedido, pe.fecha, c.nombre, c.apellidos\n"
        "  FROM pedido pe\n  JOIN cliente c ON c.id_cliente = pe.id_cliente\n ORDER BY pe.fecha DESC;"),
    "Insertar proveedor": (
        "INSERT INTO proveedor (nit, nombre, direccion)\n"
        "VALUES ('900111222-1', 'Proveedor Consola S.A.S.', 'Calle 1 # 2-3, Barranquilla');"),
    "Actualizar precio": "UPDATE producto SET precio_unitario = precio_unitario * 1.05 WHERE codigo = 'PER-001';",
    "Error: identificación repetida (UNIQUE)": (
        "INSERT INTO cliente (tipo_doc, identificacion, nombre, apellidos, direccion, fecha_nacimiento)\n"
        "VALUES ('CC', '1045678912', 'Duplicado', 'Prueba', 'Calle 1', '2000-01-01');"),
    "Error: borrar cliente con pedidos (FK)": "DELETE FROM cliente WHERE id_cliente = 1;",
    "Error: borrar proveedor con productos (FK)": "DELETE FROM proveedor WHERE id_proveedor = 1;",
    "Error: NIT con DV equivocado (CHECK)": (
        "INSERT INTO proveedor (nit, nombre, direccion)\nVALUES ('900111222-5', 'Proveedor DV malo', 'Calle 1');"),
    "Error: precio negativo (CHECK)": "UPDATE producto SET precio_unitario = -1 WHERE id_producto = 1;",
}


@app.route("/consola", methods=["GET", "POST"])
def consola():
    d = bd()
    script = request.form.get("sql", "") if request.method == "POST" else ""
    resultados, error = [], None
    if request.method == "POST" and script.strip():
        try:
            resultados = d.ejecutar_script(script)
        except DBError as e:
            error = str(e)
    tablas = [(t, d.valor(f'SELECT COUNT(*) FROM "{t}"')) for (t,) in d.consultar(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name",
        registrar=False).filas]
    return render_template("consola.html", menu="consola", script=script, resultados=resultados,
                           error=error, tablas=tablas, ejemplos=EJEMPLOS_SQL)


# ---------------------------------------------------------------- modelo E-R
ENTIDADES_ER = {
    "PROVEEDOR": ["PK id_proveedor", "   nit           UQ,CK", "   nombre", "   direccion"],
    "PRODUCTO": ["PK id_producto", "   codigo           UQ", "   nombre", "   precio_unitario  CK",
                 "FK id_proveedor"],
    "CLIENTE": ["PK id_cliente", "   tipo_doc         CK", "   identificacion UQ,CK", "   nombre",
                "   apellidos", "   direccion", "   fecha_nacimiento CK"],
    "PEDIDO": ["PK id_pedido", "FK id_cliente", "   fecha"],
    "DETALLE_PEDIDO": ["PK FK id_pedido", "PK FK id_producto", "   cantidad         CK", "   precio_compra    CK"],
}


def diagrama_er():
    """Dibuja el diagrama entidad-relación con caracteres de caja."""
    ancho, alto = 92, 24
    lienzo = [[" "] * ancho for _ in range(alto)]

    def poner(x, y, texto):
        for i, ch in enumerate(texto):
            lienzo[y][x + i] = ch

    def caja(x, y, nombre, w=26):
        campos = ENTIDADES_ER[nombre]
        poner(x, y, "┌" + "─" * (w - 2) + "┐")
        poner(x, y + 1, "│" + nombre.center(w - 2) + "│")
        poner(x, y + 2, "├" + "─" * (w - 2) + "┤")
        for i, c in enumerate(campos):
            poner(x, y + 3 + i, "│ " + c.ljust(w - 3) + "│")
        poner(x, y + 3 + len(campos), "└" + "─" * (w - 2) + "┘")

    def horizontal(x1, x2, y):  # de la entidad "1" (izquierda) a la "N" (derecha)
        poner(x1, y, "┤" + "─" * (x2 - x1 - 2) + "<")
        poner(x1 + 1, y - 1, "1")
        poner(x2 - 2, y - 1, "N")

    def vertical(x, y1, y2):  # de la entidad "1" (arriba) a la "N" (abajo)
        poner(x, y1 - 1, "┬")
        poner(x, y2 + 1, "┴")
        for y in range(y1, y2 + 1):
            poner(x, y, "│")
        poner(x, y2, "Λ")
        poner(x + 2, y1, "1")
        poner(x + 2, y2, "N")

    caja(33, 0, "PROVEEDOR")
    caja(66, 0, "PRODUCTO")
    caja(0, 12, "CLIENTE")
    caja(33, 12, "PEDIDO")
    caja(66, 12, "DETALLE_PEDIDO")
    horizontal(58, 66, 3)    # PROVEEDOR 1 ──< N PRODUCTO
    horizontal(25, 33, 15)   # CLIENTE   1 ──< N PEDIDO
    horizontal(58, 66, 15)   # PEDIDO    1 ──< N DETALLE_PEDIDO
    vertical(78, 9, 11)      # PRODUCTO  1 ──< N DETALLE_PEDIDO
    return "\n".join("".join(f).rstrip() for f in lienzo).rstrip()


# Modelo relacional: (tabla, [(columna, es_pk, referencia_fk)])
MODELO_RELACIONAL = [
    ("PROVEEDOR", [("id_proveedor", True, None), ("nit", False, None), ("nombre", False, None),
                   ("direccion", False, None)]),
    ("CLIENTE", [("id_cliente", True, None), ("tipo_doc", False, None), ("identificacion", False, None),
                 ("nombre", False, None), ("apellidos", False, None), ("direccion", False, None),
                 ("fecha_nacimiento", False, None)]),
    ("PRODUCTO", [("id_producto", True, None), ("codigo", False, None), ("nombre", False, None),
                  ("precio_unitario", False, None), ("id_proveedor", False, "PROVEEDOR")]),
    ("PEDIDO", [("id_pedido", True, None), ("id_cliente", False, "CLIENTE"), ("fecha", False, None)]),
    ("DETALLE_PEDIDO", [("id_pedido", True, "PEDIDO"), ("id_producto", True, "PRODUCTO"),
                        ("cantidad", False, None), ("precio_compra", False, None)]),
]

TABLAS = ["cliente", "producto", "proveedor", "pedido", "detalle_pedido"]


@app.route("/modelo")
def modelo():
    vista = request.args.get("v", "er")
    contexto_vista = {}
    if vista == "relacional":
        contexto_vista["relacional"] = MODELO_RELACIONAL
    elif vista == "diccionario":
        t = request.args.get("t", "cliente")
        if t not in TABLAS:
            abort(404)
        d = bd()
        contexto_vista.update(
            tabla_actual=t,
            columnas=d.consultar(f"SELECT name AS columna, type AS tipo, \"notnull\" AS not_null, "
                                 f"dflt_value AS defecto, pk FROM pragma_table_info('{t}')", registrar=False),
            fks=d.consultar(f"SELECT \"from\" AS columna, \"table\" AS referencia, \"to\" AS columna_ref, "
                            f"on_update, on_delete FROM pragma_foreign_key_list('{t}')", registrar=False),
            restricciones=d.valor("SELECT sql FROM sqlite_master WHERE name = ?", (t,)),
        )
    elif vista == "ddl":
        contexto_vista["ddl"] = (SQL_DIR / "schema.sql").read_text(encoding="utf-8")
    else:
        vista = "er"
        contexto_vista["diagrama"] = diagrama_er()
    return render_template("modelo.html", menu="modelo", vista=vista, tablas=TABLAS, **contexto_vista)


# ---------------------------------------------------------------- sistema
DESCARGAS = {"kstore.db": DB_PATH, "schema.sql": SQL_DIR / "schema.sql", "seed.sql": SQL_DIR / "seed.sql",
             "consultas.sql": SQL_DIR / "consultas.sql", "ejemplos_dml.sql": SQL_DIR / "ejemplos_dml.sql"}


@app.route("/sistema")
def sistema():
    return render_template("sistema.html", menu="sistema", integrantes=INTEGRANTES, descargas=DESCARGAS)


@app.route("/sistema/reiniciar", methods=["POST"])
def reiniciar():
    bd().reiniciar()
    session.pop("carrito", None)
    flash("Base de datos reiniciada con los datos de ejemplo.", "ok")
    return redirect(url_for("sistema"))


@app.route("/sistema/limpiar", methods=["POST"])
def limpiar_bitacora():
    BITACORAS.pop(session.get("sid"), None)
    return redirect(request.referrer or url_for("inicio"))


@app.route("/descargar/<nombre>")
def descargar(nombre):
    if nombre not in DESCARGAS:
        abort(404)
    return send_file(DESCARGAS[nombre], as_attachment=True, download_name=nombre)


@app.route("/health")
def health():
    """Ruta liviana para el ping de cron-job.org: mantiene despierta la app en Render.
    No toca la base de datos ni crea sesión (no genera bitácora en memoria)."""
    return "ok", 200, {"Content-Type": "text/plain; charset=utf-8", "Cache-Control": "no-store"}


@app.errorhandler(404)
def no_encontrado(_):
    return render_template("error.html", menu="", mensaje="404 · La página no existe."), 404


if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))
