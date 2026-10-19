"""KStore S.A.S. - Sistema de Gestión de Ventas.

Interfaz web con estilo de terminal (ncurses / menuconfig) hecha en Streamlit,
sobre una base de datos relacional SQLite.

Ejecutar:  streamlit run app.py
"""
import html
import sqlite3
from datetime import date, datetime

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from db import DB_PATH, SQL_DIR, Database, DBError, cargar_reportes, init_db
from documentos import formatear, normalizar

# ---------------------------------------------------------------- datos fijos
EMPRESA = "KStore S.A.S."
NIT_EMPRESA = "901.555.777-4"
VERSION = "1.0"
CURSO = "Laboratorio 01 - Bases de Datos"
INTEGRANTES = [
    "Andrés Parejo",
    "Valeria Flórez",
    "Víctor Mendoza",
    "Santiago Molina",
    "Sara Ibáñez",
]
IVA = 0.19
METODOS_PAGO = ["EFECTIVO", "TARJETA", "TRANSFERENCIA", "CREDITO"]
COLUMNAS_DINERO = {
    "precio", "precio_unitario", "valor", "subtotal", "iva", "total", "ingresos",
    "vendido", "total_comprado", "comision_ganada",
}

st.set_page_config(page_title="KStore · Ventas", page_icon="🖥️", layout="wide")

# ---------------------------------------------------------------- estilos
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
:root {
  /* paleta "Campbell" de la terminal de Windows */
  --fondo: #0C0C0C; --fondo2: #1E1E1E; --gris: #A0A0A0; --texto: #CCCCCC; --tenue: #767676;
}
.stApp, .stApp p, .stApp label, .stApp input, .stApp textarea, .stApp button {
  font-family: 'JetBrains Mono', 'Courier New', monospace !important;
}
header[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"], footer { display: none !important; }
.block-container { padding: 0.5rem 1.2rem 0.6rem 1.2rem !important; max-width: 100% !important; }
[data-testid="stVerticalBlock"] { gap: 0.55rem; }

/* barras superior e inferior */
.tb-top { background: var(--texto); color: #000; padding: 2px 10px; display: flex;
          justify-content: space-between; font-weight: 600; white-space: nowrap; overflow: hidden; }
.tb-bar { background: var(--gris); color: #000; padding: 2px 10px; display: flex; flex-wrap: wrap;
          justify-content: space-between; gap: 4px 16px; }
.tb-bar b { color: var(--fondo); }

/* cajas con borde doble */
.st-key-caja_menu, .st-key-caja_main, .st-key-caja_log {
  border: 3px double var(--gris); padding: 10px 12px 12px 12px; background: var(--fondo);
}
.st-key-caja_log { padding: 6px 12px; }
.tb-h { display: inline-block; background: var(--gris); color: var(--fondo); padding: 0 8px;
        font-weight: 600; margin-bottom: 2px; }
.tb-h2 { color: var(--texto); font-weight: 700; margin: 4px 0 0 0; }
.tb-help { color: var(--tenue); font-size: 0.85rem; }

/* menú lateral */
.st-key-menu .stButton > button { background: transparent !important; border: none !important; color: var(--texto) !important;
  justify-content: flex-start !important; padding: 0 8px !important; min-height: 1.8rem !important; }
.st-key-menu button p::first-letter { font-weight: 700; text-decoration: underline; }
.st-key-menu .stButton > button:hover, .st-key-menu .stButton > button:focus-visible { background: var(--fondo2) !important; }
.st-key-menu .stButton > button[kind="primary"] {
  background: var(--texto) !important; color: #000 !important; }
.st-key-menu button[kind="primary"] p::first-letter { color: var(--fondo); }
.st-key-menu [data-testid="stVerticalBlock"] { gap: 0 !important; }

/* botones de acción tipo <Select> */
.stButton > button, .stFormSubmitButton > button, .stDownloadButton > button {
  border-radius: 0 !important; background: var(--gris) !important; color: #000 !important;
  border: none !important; font-weight: 600; }
.stButton > button:hover, .stFormSubmitButton > button:hover, .stDownloadButton > button:hover {
  background: var(--texto) !important; }
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primaryFormSubmit"],
.stButton > button[data-testid="stBaseButton-primary"], .stFormSubmitButton > button[data-testid="stBaseButton-primaryFormSubmit"] {
  background: var(--texto) !important; color: #000 !important; }
.stButton button p, .stFormSubmitButton button p, .stDownloadButton button p { white-space: nowrap; }
.stButton > button:disabled { background: #333 !important; color: #777 !important; }

/* entradas */
[data-testid="stWidgetLabel"] p { color: var(--gris) !important; }
[data-testid="stForm"] { border: 1px solid var(--gris) !important; border-radius: 0 !important; }
[data-testid="stRadio"] label p { color: var(--texto); }

/* mensajes */
.tb-msg { padding: 4px 10px; margin: 2px 0 6px 0; border-left: 4px solid; }
.tb-ok   { color: var(--texto); border-color: var(--texto); background: var(--fondo2); }
.tb-err  { color: var(--fondo); border-color: var(--gris); background: var(--texto); font-weight: 700; }
.tb-warn { color: var(--texto); border: 1px dashed var(--texto); border-left: 4px solid var(--texto); background: var(--fondo2); }

/* bloques de texto tipo terminal */
/* fuentes del sistema con caracteres de caja (─│┌┐) del mismo ancho para que los dibujos alineen */
.stApp .tb-pre, .stApp .tb-log { font-family: Consolas, Menlo, 'DejaVu Sans Mono', 'Liberation Mono', 'Courier New', monospace !important; }
.tb-pre { white-space: pre; overflow-x: auto; color: var(--texto);
          line-height: 1.2; margin: 0; font-size: 0.9rem; }
.tb-pre .k { color: var(--gris); } .tb-pre .v { color: var(--texto); font-weight: 700; }
.tb-pre .r { background: var(--texto); color: var(--fondo); }
.tb-pre .g { color: var(--texto); } .tb-pre .d { color: var(--tenue); }
.tb-log { font-size: 0.8rem; height: 150px; overflow-y: auto;
          white-space: pre; line-height: 1.35; }
.tb-log .t { color: var(--tenue); } .tb-log .ok { color: var(--gris); }
.tb-log .err { background: var(--texto); color: var(--fondo); } .tb-log .tx { color: var(--texto); font-weight: 700; }
.tb-count { color: var(--texto); padding-top: 2rem; }
</style>
"""

# Atajos de teclado: 0-9 eligen opción del menú, flechas navegan, Esc vuelve al inicio
ATAJOS_JS = """
<script>
(function () {
  const doc = window.parent.document;
  if (doc.getElementById('tb-atajos')) return;
  const s = doc.createElement('script');
  s.id = 'tb-atajos';
  s.textContent = `
    document.addEventListener('keydown', function (e) {
      const t = e.target, tag = (t.tagName || '').toLowerCase();
      if (tag === 'input' || tag === 'textarea' || tag === 'select' || t.isContentEditable) return;
      if (e.ctrlKey || e.metaKey || e.altKey) return;
      const menu = Array.from(document.querySelectorAll('.st-key-menu button'));
      if (!menu.length) return;
      if (/^[0-9]$/.test(e.key)) {
        const b = menu.find(function (x) { return x.innerText.trim().charAt(0) === e.key; });
        if (b) { e.preventDefault(); b.click(); }
      } else if (e.key === 'Escape') {
        e.preventDefault(); menu[0].click();
      } else if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
        const activo = document.activeElement;
        let i = menu.indexOf(activo);
        if (i === -1 && activo !== document.body) return;
        if (i === -1) i = menu.findIndex(function (x) { return x.getAttribute('kind') === 'primary'; });
        e.preventDefault();
        i = (i + (e.key === 'ArrowDown' ? 1 : -1) + menu.length) % menu.length;
        menu[i].focus();
      }
    });
  `;
  doc.head.appendChild(s);
})();
</script>
"""

LETRAS_BANNER = {
    "K": [" _  __", "| |/ /", "| ' < ", "|_|\\_\\", "      "],
    "e": ["     ", " ___ ", "/ -_)", "\\___|", "     "],
    "r": ["     ", " _ _ ", "| '_|", "|_|  ", "     "],
    "S": ["  ___ ", " / __|", " \\__ \\", " |___/", "      "],
    "t": [" _   ", "| |_ ", "|  _|", " \\__|", "     "],
    "o": ["     ", " ___ ", "/ _ \\", "\\___/", "     "],
}


def banner(texto):
    return "\n".join("".join(LETRAS_BANNER[c][i] for c in texto) for i in range(5))


# ---------------------------------------------------------------- estado
@st.cache_resource
def preparar_bd():
    init_db()
    return True


preparar_bd()
for clave, inicial in [("log", []), ("menu", "inicio"), ("carrito", []), ("historial_sql", [])]:
    if clave not in st.session_state:
        st.session_state[clave] = inicial
db = Database(st.session_state.log)


# ---------------------------------------------------------------- utilidades
def dinero(v):
    return "$ " + f"{(v or 0):,.0f}".replace(",", ".")


def esc(texto):
    return html.escape(str(texto))


def titulo(texto):
    st.html(f'<div class="tb-h">[ {esc(texto)} ]</div>')


def subtitulo(texto):
    st.html(f'<div class="tb-h2">── {esc(texto)} ──</div>')


def ayuda(texto):
    st.html(f'<div class="tb-help">{esc(texto)}</div>')


def pre(texto_html):
    st.html(f'<div class="tb-pre">{texto_html}</div>')


def mensaje(tipo, texto):
    marca = {"ok": "[ OK ]", "err": "[ERROR]", "warn": "[ ! ]"}[tipo]
    st.html(f'<div class="tb-msg tb-{tipo}">{marca} {esc(texto)}</div>')


def avisar_luego(tipo, texto):
    """Mensaje que se muestra después del st.rerun()."""
    st.session_state.flash = (tipo, texto)


def mostrar_aviso():
    aviso = st.session_state.pop("flash", None)
    if aviso:
        mensaje(*aviso)


def intentar(accion, exito, limpiar_prefijo=None, ir_a=None):
    """Ejecuta una operación; si falla muestra el error de la BD."""
    try:
        accion()
    except DBError as e:
        mensaje("err", str(e))
        return
    if limpiar_prefijo:
        for k in [k for k in st.session_state if str(k).startswith(limpiar_prefijo)]:
            del st.session_state[k]
    if ir_a:
        st.session_state["_ir_a"] = ir_a
    avisar_luego("ok", exito)
    st.rerun()


def submenu(clave, opciones):
    """Sub-opciones de un módulo (Listar / Nuevo / Editar / Eliminar)."""
    destino = st.session_state.pop("_ir_a", None)
    if destino and destino[0] == clave:
        st.session_state[clave] = destino[1]
    return st.radio("Acción", opciones, horizontal=True, key=clave, label_visibility="collapsed")


def tabla(df, altura=None):
    config = {}
    for col in df.columns:
        if col in COLUMNAS_DINERO:
            config[col] = st.column_config.NumberColumn(col, format="localized")
        elif col in ("descuento",):
            config[col] = st.column_config.NumberColumn(col, format="percent")
    kwargs = {"height": altura} if altura else {}
    st.dataframe(df, hide_index=True, width="stretch", column_config=config, **kwargs)


def opciones_de(sql):
    """Devuelve (lista_ids, diccionario id -> etiqueta) para un selectbox."""
    df = db.consultar(sql, registrar=False)
    ids = df.iloc[:, 0].tolist()
    return ids, dict(zip(ids, df.iloc[:, 1]))


# ---------------------------------------------------------------- CRUD genérico
ENTIDADES = {
    "clientes": {
        "titulo": "Clientes", "singular": "Cliente", "tabla": "cliente", "pk": "id_cliente",
        "listar": """SELECT id_cliente AS id, tipo, tipo_doc, formato_doc(tipo_doc, documento) AS documento,
                            nombre, email,
                            telefono, ciudad, fecha_registro FROM cliente""",
        "orden": "nombre", "buscar": ["documento", "nombre", "email", "ciudad"],
        "etiqueta": "formato_doc(tipo_doc, documento) || '  ' || nombre",
        "validar": lambda v: validar_cliente(v),
        "campos": [
            {"col": "tipo", "label": "Tipo de cliente", "tipo": "select", "opciones": ["PERSONA", "EMPRESA"]},
            {"col": "tipo_doc", "label": "Tipo de documento", "tipo": "select", "opciones": ["CC", "NIT", "CE"]},
            {"col": "documento", "label": "Número de documento",
             "placeholder": "CC 1.045.678.912 · CE 845.123 · NIT 900.123.456-8",
             "mostrar": lambda fila: formatear(fila.get("tipo_doc"), fila.get("documento"))},
            {"col": "nombre", "label": "Nombre o razón social"},
            {"col": "email", "label": "Correo electrónico"},
            {"col": "telefono", "label": "Teléfono"},
            {"col": "ciudad", "label": "Ciudad"},
        ],
    },
    "productos": {
        "titulo": "Productos", "singular": "Producto", "tabla": "producto", "pk": "id_producto",
        "listar": """SELECT p.id_producto AS id, p.codigo, p.nombre, c.nombre AS categoria, p.precio,
                            p.stock, p.stock_minimo,
                            CASE WHEN p.stock <= p.stock_minimo THEN 'BAJO' ELSE 'OK' END AS alerta,
                            CASE p.activo WHEN 1 THEN 'SI' ELSE 'NO' END AS activo
                       FROM producto p JOIN categoria c ON c.id_categoria = p.id_categoria""",
        "orden": "codigo", "buscar": ["codigo", "nombre", "categoria", "alerta"],
        "etiqueta": "codigo || '  ' || nombre",
        "campos": [
            {"col": "codigo", "label": "Código"},
            {"col": "nombre", "label": "Nombre del producto"},
            {"col": "id_categoria", "label": "Categoría", "tipo": "fk",
             "sql": "SELECT id_categoria, nombre FROM categoria ORDER BY nombre"},
            {"col": "precio", "label": "Precio (sin IVA)", "tipo": "dinero"},
            {"col": "stock", "label": "Stock", "tipo": "entero"},
            {"col": "stock_minimo", "label": "Stock mínimo", "tipo": "entero", "defecto": 5},
            {"col": "activo", "label": "Activo (se puede vender)", "tipo": "bool"},
        ],
    },
    "categorias": {
        "titulo": "Categorías", "singular": "Categoría", "tabla": "categoria", "pk": "id_categoria",
        "listar": """SELECT c.id_categoria AS id, c.nombre, c.descripcion,
                            COUNT(p.id_producto) AS productos
                       FROM categoria c LEFT JOIN producto p ON p.id_categoria = c.id_categoria
                      GROUP BY c.id_categoria""",
        "orden": "nombre", "buscar": ["nombre", "descripcion"],
        "etiqueta": "nombre",
        "campos": [
            {"col": "nombre", "label": "Nombre"},
            {"col": "descripcion", "label": "Descripción", "tipo": "area"},
        ],
    },
    "vendedores": {
        "titulo": "Vendedores", "singular": "Vendedor", "tabla": "vendedor", "pk": "id_vendedor",
        "listar": """SELECT id_vendedor AS id, formato_doc('CC', documento) AS cedula, nombre, email,
                            comision * 100 AS comision_pct,
                            CASE activo WHEN 1 THEN 'SI' ELSE 'NO' END AS activo
                       FROM vendedor""",
        "orden": "nombre", "buscar": ["cedula", "nombre", "email"],
        "etiqueta": "formato_doc('CC', documento) || '  ' || nombre",
        "validar": lambda v: v.update(documento=normalizar("CC", v["documento"])),
        "campos": [
            {"col": "documento", "label": "Cédula de ciudadanía", "placeholder": "1.045.678.912",
             "mostrar": lambda fila: formatear("CC", fila.get("documento"))},
            {"col": "nombre", "label": "Nombre completo"},
            {"col": "email", "label": "Correo electrónico"},
            {"col": "comision", "label": "Comisión (0.03 = 3 %)", "tipo": "pct", "defecto": 0.02},
            {"col": "activo", "label": "Activo", "tipo": "bool"},
        ],
    },
}


def validar_cliente(valores):
    """Revisa el documento antes de enviarlo; la BD lo vuelve a validar con CHECK."""
    if valores["tipo"] == "EMPRESA" and valores["tipo_doc"] != "NIT":
        raise ValueError("Un cliente EMPRESA se identifica con NIT.")
    if valores["tipo"] == "PERSONA" and valores["tipo_doc"] == "NIT":
        raise ValueError("Un cliente PERSONA se identifica con CC o CE.")
    valores["documento"] = normalizar(valores["tipo_doc"], valores["documento"])


def validar(cfg, valores):
    """Aplica la validación propia de la entidad; muestra el error si falla."""
    try:
        if "validar" in cfg:
            cfg["validar"](valores)
    except ValueError as e:
        mensaje("err", str(e))
        return False
    return True


def widget_campo(campo, actual, clave):
    tipo = campo.get("tipo", "texto")
    label = campo["label"]
    if actual is None:
        actual = campo.get("defecto")
    if tipo == "select":
        ops = campo["opciones"]
        return st.selectbox(label, ops, index=ops.index(actual) if actual in ops else 0, key=clave)
    if tipo == "fk":
        ids, nombres = opciones_de(campo["sql"])
        return st.selectbox(label, ids, index=ids.index(actual) if actual in ids else 0,
                            format_func=lambda i: f"{i} - {nombres[i]}", key=clave)
    if tipo == "dinero":
        return st.number_input(label, value=float(actual or 0), step=1000.0, format="%.0f", key=clave)
    if tipo == "entero":
        return int(st.number_input(label, value=int(actual or 0), step=1, key=clave))
    if tipo == "pct":
        return st.number_input(label, value=float(actual or 0), step=0.005, format="%.3f", key=clave)
    if tipo == "bool":
        return 1 if st.checkbox(label, value=bool(1 if actual is None else actual), key=clave) else 0
    if tipo == "area":
        valor = st.text_area(label, value=actual or "", key=clave, height=80)
    else:
        valor = st.text_input(label, value=actual or "", key=clave, placeholder=campo.get("placeholder"))
    # Un texto vacío se guarda como NULL para que actúe la restricción NOT NULL
    return valor.strip() or None


def campos_formulario(cfg, actual, prefijo):
    valores = {}
    columnas = st.columns(2)
    for i, campo in enumerate(cfg["campos"]):
        with columnas[i % 2]:
            valor_actual = campo["mostrar"](actual) if "mostrar" in campo and actual else actual.get(campo["col"])
            valores[campo["col"]] = widget_campo(campo, valor_actual, f"{prefijo}_{campo['col']}")
    return valores


def pagina_crud(clave):
    cfg = ENTIDADES[clave]
    tabla_bd, pk = cfg["tabla"], cfg["pk"]
    accion = submenu(f"sub_{clave}", ["Listar", "Nuevo", "Editar", "Eliminar"])

    if accion == "Listar":
        c1, c2 = st.columns([4, 1])
        texto = c1.text_input("Buscar", placeholder="Escriba para filtrar...", key=f"buscar_{clave}")
        sql = f"SELECT * FROM ({cfg['listar']}) AS t"
        params = []
        if texto.strip():
            # Se ignoran los puntos para encontrar 1045678912 aunque se muestre 1.045.678.912
            sql += " WHERE " + " OR ".join(f"REPLACE({c}, '.', '') LIKE ?" for c in cfg["buscar"])
            params = [f"%{texto.strip().replace('.', '')}%"] * len(cfg["buscar"])
        sql += f" ORDER BY {cfg['orden']}"
        df = db.consultar(sql, params)
        with c2:
            st.html(f'<div class="tb-count">{len(df)} registro(s)</div>')
        tabla(df)
        return

    if accion == "Nuevo":
        prefijo = f"nuevo_{tabla_bd}"
        with st.form(f"form_{prefijo}"):
            valores = campos_formulario(cfg, {}, prefijo)
            enviar = st.form_submit_button("< Guardar >", type="primary")
        if enviar and validar(cfg, valores):
            columnas = list(valores)
            sql = (f"INSERT INTO {tabla_bd} ({', '.join(columnas)}) "
                   f"VALUES ({', '.join('?' * len(columnas))})")
            intentar(lambda: db.ejecutar(sql, list(valores.values())),
                     f"{cfg['singular']} registrado correctamente.",
                     limpiar_prefijo=prefijo, ir_a=(f"sub_{clave}", "Listar"))
        ayuda("Las restricciones (UNIQUE, CHECK, NOT NULL, FOREIGN KEY) las valida la base de datos.")
        return

    ids, etiquetas = opciones_de(f"SELECT {pk}, {cfg['etiqueta']} AS e FROM {tabla_bd} ORDER BY e")
    if not ids:
        mensaje("warn", "No hay registros.")
        return
    elegido = st.selectbox(f"{cfg['singular']}", ids, format_func=lambda i: f"#{i}  {etiquetas[i]}",
                           key=f"sel_{accion}_{clave}")
    actual = db.fila(f"SELECT * FROM {tabla_bd} WHERE {pk} = ?", (elegido,))

    if accion == "Editar":
        prefijo = f"editar_{tabla_bd}_{elegido}"
        with st.form(f"form_{prefijo}"):
            valores = campos_formulario(cfg, actual, prefijo)
            enviar = st.form_submit_button("< Actualizar >", type="primary")
        if enviar and validar(cfg, valores):
            asignaciones = ", ".join(f"{c} = ?" for c in valores)
            sql = f"UPDATE {tabla_bd} SET {asignaciones} WHERE {pk} = ?"
            intentar(lambda: db.ejecutar(sql, list(valores.values()) + [elegido]),
                     f"{cfg['singular']} #{elegido} actualizado.", limpiar_prefijo=prefijo)
        return

    # Eliminar
    ancho = max(len(k) for k in actual)
    pre("\n".join(f'<span class="k">{esc(k.ljust(ancho))}</span> : <span class="v">{esc(v)}</span>'
                  for k, v in actual.items()))
    ayuda("Si el registro tiene datos relacionados, la base de datos rechaza el borrado (ON DELETE RESTRICT).")
    confirmar = st.checkbox("Confirmo que deseo eliminar este registro", key=f"conf_{clave}_{elegido}")
    if st.button("< Eliminar >", disabled=not confirmar, key=f"btn_del_{clave}"):
        intentar(lambda: db.ejecutar(f"DELETE FROM {tabla_bd} WHERE {pk} = ?", (elegido,)),
                 f"{cfg['singular']} #{elegido} eliminado.")


# ---------------------------------------------------------------- módulos
def pagina_inicio():
    total_clientes = db.valor("SELECT COUNT(*) FROM cliente")
    total_productos = db.valor("SELECT COUNT(*) FROM producto")
    bajo_stock = db.valor("SELECT COUNT(*) FROM producto WHERE stock <= stock_minimo")
    ventas = db.valor("SELECT COUNT(*) FROM venta WHERE estado <> 'ANULADA'")
    anuladas = db.valor("SELECT COUNT(*) FROM venta WHERE estado = 'ANULADA'")
    pendientes = db.valor("SELECT COUNT(*) FROM venta WHERE estado = 'PENDIENTE'")
    facturado = db.valor("SELECT COALESCE(SUM(total), 0) FROM v_venta_resumen WHERE estado <> 'ANULADA'")
    mes = date.today().strftime("%Y-%m")
    facturado_mes = db.valor("SELECT COALESCE(SUM(total), 0) FROM v_venta_resumen "
                             "WHERE estado <> 'ANULADA' AND strftime('%Y-%m', fecha) = ?", (mes,))
    por_cobrar = db.valor("SELECT COALESCE(SUM(total), 0) FROM v_venta_resumen WHERE estado = 'PENDIENTE'")
    ticket = facturado / ventas if ventas else 0

    izq, der = st.columns([1, 1])
    with izq:
        pre(f'<span class="g">{esc(banner("KStore"))}</span>\n'
            f'<span class="d">  {esc(EMPRESA)}  ·  NIT {NIT_EMPRESA}</span>\n'
            f'<span class="d">  Sistema de Gestión de Ventas v{VERSION}</span>\n\n'
            '<span class="k">  Integrantes:</span>\n'
            + "\n".join(f'<span class="v">   · {esc(n)}</span>' for n in INTEGRANTES))
    with der:
        subtitulo("Status")

        def linea(k, v, clase="v"):
            return f'<span class="k">{esc(k.ljust(19))}</span><span class="{clase}">{esc(v)}</span>'

        pre("\n".join([
            linea("Base de datos:", f"SQLite {sqlite3.sqlite_version}  ({DB_PATH.name})"),
            linea("Clientes:", total_clientes),
            linea("Productos:", f"{total_productos}"),
            linea("Stock bajo:", f"{bajo_stock} producto(s)", "r" if bajo_stock else "g"),
            linea("Ventas válidas:", f"{ventas}   (anuladas: {anuladas})"),
            linea("Por cobrar:", f"{dinero(por_cobrar)}  ({pendientes} pendiente/s)"),
            linea(f"Facturado {mes}:", dinero(facturado_mes)),
            linea("Facturado total:", dinero(facturado)),
            linea("Ticket promedio:", dinero(ticket)),
        ]))

    c1, c2 = st.columns([3, 2])
    with c1:
        subtitulo("Últimas ventas")
        tabla(db.consultar("SELECT id_venta AS id, fecha, cliente, vendedor, estado, total "
                           "FROM v_venta_resumen ORDER BY fecha DESC LIMIT 6", registrar=False))
    with c2:
        subtitulo("Alertas de inventario")
        df = db.consultar("SELECT codigo, nombre, stock, stock_minimo AS minimo FROM producto "
                          "WHERE stock <= stock_minimo ORDER BY stock", registrar=False)
        if df.empty:
            mensaje("ok", "Todo el inventario está por encima del mínimo.")
        else:
            tabla(df)


def pagina_ventas():
    accion = submenu("sub_ventas", ["Nueva venta", "Historial", "Factura", "Gestionar"])
    if accion == "Nueva venta":
        nueva_venta()
    elif accion == "Historial":
        historial_ventas()
    elif accion == "Factura":
        ids, etiquetas = opciones_de("SELECT id_venta, cliente || '  ' || fecha || '  [' || estado || ']' "
                                     "FROM v_venta_resumen ORDER BY id_venta DESC")
        if not ids:
            mensaje("warn", "No hay ventas registradas.")
            return
        inicial = st.session_state.get("ultima_factura")
        elegido = st.selectbox("Venta", ids, index=ids.index(inicial) if inicial in ids else 0,
                               format_func=lambda i: f"#{i:05d}  {etiquetas[i]}")
        pre(esc(factura_texto(elegido)))
    else:
        gestionar_venta()


def nueva_venta():
    carrito = st.session_state.carrito
    clientes, n_clientes = opciones_de("SELECT id_cliente, formato_doc(tipo_doc, documento) || '  ' || nombre AS e "
                                      "FROM cliente ORDER BY nombre")
    vendedores, n_vendedores = opciones_de("SELECT id_vendedor, nombre FROM vendedor WHERE activo = 1 ORDER BY nombre")
    if not clientes or not vendedores:
        mensaje("warn", "Se necesita al menos un cliente y un vendedor activo.")
        return

    c1, c2, c3 = st.columns([3, 2, 2])
    id_cliente = c1.selectbox("Cliente", clientes, format_func=lambda i: n_clientes[i], key="venta_cliente")
    id_vendedor = c2.selectbox("Vendedor", vendedores, format_func=lambda i: n_vendedores[i], key="venta_vendedor")
    metodo = c3.selectbox("Método de pago", METODOS_PAGO, key="venta_metodo")

    productos = db.consultar("SELECT id_producto, codigo, nombre, precio, stock FROM producto "
                             "WHERE activo = 1 ORDER BY codigo", registrar=False).set_index("id_producto")
    subtitulo("Agregar producto")
    with st.form("form_item", clear_on_submit=True):
        a, b, c, d = st.columns([5, 1, 1, 1], vertical_alignment="bottom")
        id_producto = a.selectbox(
            "Producto", productos.index.tolist(),
            format_func=lambda i: (f"{productos.at[i, 'codigo']}  {productos.at[i, 'nombre']}  |  "
                                   f"{dinero(productos.at[i, 'precio'])}  |  stock {productos.at[i, 'stock']}"))
        cantidad = int(b.number_input("Cantidad", min_value=1, value=1, step=1))
        descuento = c.selectbox("Descuento", [0, 5, 10, 15, 20], format_func=lambda x: f"{x} %")
        agregar = d.form_submit_button("< Agregar >")
    if agregar:
        p = productos.loc[id_producto]
        existente = next((it for it in carrito if it["id_producto"] == id_producto), None)
        ya = existente["cantidad"] if existente else 0
        if ya + cantidad > p["stock"]:
            mensaje("warn", f"Solo hay {p['stock']} unidad(es) de {p['nombre']} (en el carrito: {ya}).")
        else:
            if existente:
                existente["cantidad"] += cantidad
                existente["descuento"] = descuento / 100
            else:
                carrito.append({"id_producto": int(id_producto), "codigo": p["codigo"], "producto": p["nombre"],
                                "cantidad": cantidad, "precio_unitario": float(p["precio"]),
                                "descuento": descuento / 100})
            st.rerun()

    subtitulo(f"Carrito ({len(carrito)} ítem/s)")
    if not carrito:
        ayuda("El carrito está vacío. Agregue productos para registrar la venta.")
        return
    df = pd.DataFrame(carrito).drop(columns=["id_producto"])
    df["valor"] = (df["cantidad"] * df["precio_unitario"] * (1 - df["descuento"])).round(0)
    tabla(df)
    subtotal = float(df["valor"].sum())
    iva = round(subtotal * IVA)
    total = round(subtotal * (1 + IVA))

    c1, c2 = st.columns([3, 2])
    with c2:
        pre(f'<span class="k">SUBTOTAL   </span>{esc(dinero(subtotal).rjust(16))}\n'
            f'<span class="k">IVA 19 %   </span>{esc(dinero(iva).rjust(16))}\n'
            f'<span class="k">TOTAL      </span><span class="v">{esc(dinero(total).rjust(16))}</span>')
    with c1:
        quitar = st.selectbox("Ítem", range(len(carrito)),
                              format_func=lambda i: f"{i + 1}. {carrito[i]['producto']} x{carrito[i]['cantidad']}",
                              key="item_quitar", label_visibility="collapsed")
        b1, b2, b3 = st.columns(3)
        if b1.button("< Quitar ítem >", width="stretch"):
            carrito.pop(quitar)
            st.rerun()
        if b2.button("< Vaciar >", width="stretch"):
            carrito.clear()
            st.rerun()
        confirmar = b3.button("< Confirmar venta >", type="primary", width="stretch")

    if confirmar:
        estado = "PENDIENTE" if metodo == "CREDITO" else "PAGADA"
        try:
            with db.transaccion() as run:
                id_venta = run("INSERT INTO venta (id_cliente, id_vendedor, metodo_pago, estado) "
                               "VALUES (?, ?, ?, ?)", (id_cliente, id_vendedor, metodo, estado)).lastrowid
                for it in carrito:
                    run("INSERT INTO detalle_venta (id_venta, id_producto, cantidad, precio_unitario, descuento) "
                        "VALUES (?, ?, ?, ?, ?)",
                        (id_venta, it["id_producto"], it["cantidad"], it["precio_unitario"], it["descuento"]))
        except DBError as e:
            mensaje("err", f"La venta no se registró (ROLLBACK): {e}")
            return
        carrito.clear()
        st.session_state.ultima_factura = id_venta
        st.session_state["_ir_a"] = ("sub_ventas", "Factura")
        avisar_luego("ok", f"Venta #{id_venta:05d} registrada por {dinero(total)}. El stock se descontó automáticamente.")
        st.rerun()


def historial_ventas():
    rango = db.fila("SELECT MIN(date(fecha)) AS desde, MAX(date(fecha)) AS hasta FROM venta")
    hoy = date.today()
    desde_def = date.fromisoformat(rango["desde"]) if rango["desde"] else hoy
    c1, c2, c3, c4 = st.columns([1, 1, 2, 2])
    desde = c1.date_input("Desde", value=desde_def, format="YYYY-MM-DD")
    hasta = c2.date_input("Hasta", value=max(hoy, desde_def), format="YYYY-MM-DD")
    estados = c3.multiselect("Estado", ["PAGADA", "PENDIENTE", "ANULADA"], default=["PAGADA", "PENDIENTE", "ANULADA"])
    texto = c4.text_input("Cliente o vendedor", placeholder="Filtrar por nombre...")
    if not estados:
        mensaje("warn", "Seleccione al menos un estado.")
        return
    sql = ("SELECT id_venta AS id, fecha, cliente, vendedor, metodo_pago, estado, items, subtotal, iva, total "
           "FROM v_venta_resumen WHERE date(fecha) BETWEEN ? AND ? "
           f"AND estado IN ({', '.join('?' * len(estados))}) ")
    params = [desde.isoformat(), hasta.isoformat()] + estados
    if texto.strip():
        sql += "AND (cliente LIKE ? OR vendedor LIKE ?) "
        params += [f"%{texto.strip()}%"] * 2
    sql += "ORDER BY fecha DESC"
    df = db.consultar(sql, params)
    tabla(df)
    validas = df[df["estado"] != "ANULADA"]
    pre(f'<span class="k">Facturas:</span> <span class="v">{len(df)}</span>   '
        f'<span class="k">Total (sin anuladas):</span> <span class="v">{esc(dinero(validas["total"].sum()))}</span>')


def factura_texto(id_venta):
    v = db.fila("SELECT r.*, c.tipo_doc, c.documento, c.ciudad, c.telefono FROM v_venta_resumen r "
                "JOIN cliente c ON c.id_cliente = r.id_cliente WHERE r.id_venta = ?", (id_venta,))
    items = db.consultar("SELECT p.codigo, p.nombre, d.cantidad, d.precio_unitario, d.descuento, "
                         "ROUND(d.cantidad * d.precio_unitario * (1 - d.descuento), 0) AS valor "
                         "FROM detalle_venta d JOIN producto p ON p.id_producto = d.id_producto "
                         "WHERE d.id_venta = ? ORDER BY p.codigo", (id_venta,), registrar=False)
    w = 80
    interior = w - 4

    def fila(izq, der=""):
        izq = izq[: interior - len(der) - 1] if der else izq[:interior]
        return "│ " + izq + " " * (interior - len(izq) - len(der)) + der + " │"

    sep = "├" + "─" * (w - 2) + "┤"
    lineas = [
        "┌" + "─" * (w - 2) + "┐",
        fila(EMPRESA.upper(), f"NIT {NIT_EMPRESA}"),
        fila("Barranquilla, Atlántico", f"FACTURA DE VENTA No. {id_venta:05d}"),
        sep,
        fila(f"Cliente : {v['cliente']}", f"{v['tipo_doc']} {formatear(v['tipo_doc'], v['documento'])}"),
        fila(f"Ciudad  : {v['ciudad']}", f"Tel. {v['telefono'] or '-'}"),
        fila(f"Fecha   : {v['fecha']}", f"Vendedor: {v['vendedor']}"),
        fila(f"Pago    : {v['metodo_pago']}", f"Estado: {v['estado']}"),
        sep,
        fila(f"{'CÓDIGO':<8} {'DESCRIPCIÓN':<28} {'CANT':>4} {'P. UNIT':>12} {'DTO':>4} {'VALOR':>12}"[:interior]),
        sep,
    ]
    for it in items.itertuples():
        lineas.append(fila(f"{it.codigo:<8} {it.nombre[:28]:<28} {it.cantidad:>4} "
                           f"{dinero(it.precio_unitario):>12} {int(it.descuento * 100):>3}% {dinero(it.valor):>12}"))
    lineas += [
        sep,
        fila("", f"SUBTOTAL {dinero(v['subtotal']):>16}"),
        fila("", f"IVA 19 % {dinero(v['iva']):>16}"),
        fila("", f"TOTAL    {dinero(v['total']):>16}"),
        "└" + "─" * (w - 2) + "┘",
    ]
    if v["estado"] == "ANULADA":
        lineas.insert(3, fila("*** FACTURA ANULADA ***".center(interior)))
    return "\n".join(lineas)


def gestionar_venta():
    ids, etiquetas = opciones_de("SELECT id_venta, cliente || '  ' || fecha || '  [' || estado || ']' "
                                 "FROM v_venta_resumen ORDER BY id_venta DESC")
    if not ids:
        mensaje("warn", "No hay ventas registradas.")
        return
    elegido = st.selectbox("Venta", ids, format_func=lambda i: f"#{i:05d}  {etiquetas[i]}", key="gestionar_venta")
    estado = db.valor("SELECT estado FROM venta WHERE id_venta = ?", (elegido,))
    pre(esc(factura_texto(elegido)))
    ayuda("Anular devuelve el stock (trigger trg_venta_anular). Eliminar borra el detalle en cascada "
          "(ON DELETE CASCADE) y también devuelve el stock si la venta no estaba anulada.")
    c1, c2, c3, c4 = st.columns([1, 1, 2, 1], vertical_alignment="center")
    if c1.button("< Marcar pagada >", disabled=estado != "PENDIENTE", width="stretch"):
        intentar(lambda: db.ejecutar("UPDATE venta SET estado = 'PAGADA' WHERE id_venta = ?", (elegido,)),
                 f"Venta #{elegido:05d} marcada como pagada.")
    if c2.button("< Anular >", disabled=estado == "ANULADA", width="stretch"):
        intentar(lambda: db.ejecutar("UPDATE venta SET estado = 'ANULADA' WHERE id_venta = ?", (elegido,)),
                 f"Venta #{elegido:05d} anulada. El stock fue devuelto.")
    confirmar = c3.checkbox("Confirmo eliminar la venta", key=f"conf_venta_{elegido}")
    if c4.button("< Eliminar >", disabled=not confirmar, width="stretch"):
        intentar(lambda: db.ejecutar("DELETE FROM venta WHERE id_venta = ?", (elegido,)),
                 f"Venta #{elegido:05d} eliminada.")


def pagina_reportes():
    reportes = cargar_reportes()
    indice = st.selectbox("Reporte", range(len(reportes)),
                          format_func=lambda i: f"{i + 1:>2}. {reportes[i]['titulo']}", key="reporte")
    rep = reportes[indice]
    if rep["descripcion"]:
        ayuda(rep["descripcion"])
    try:
        df = db.consultar(rep["sql"])
    except DBError as e:
        mensaje("err", str(e))
        return
    if rep["grafico"] and not df.empty:
        izq, der = st.columns([3, 2])
        with izq:
            tabla(df)
        with der:
            x, y = rep["grafico"]
            st.bar_chart(df, x=x, y=y, color="#CCCCCC", height=300)
    else:
        tabla(df)
    with st.expander("Ver SQL de la consulta"):
        st.code(rep["sql"], language="sql")
    ayuda(f"Fuente: sql/consultas.sql  ·  {len(df)} fila(s)")


EJEMPLOS_SQL = {
    "(elegir un ejemplo)": "",
    "Listar tablas": "SELECT name, type FROM sqlite_master WHERE type IN ('table', 'view') ORDER BY name;",
    "Productos más caros": "SELECT codigo, nombre, precio FROM producto ORDER BY precio DESC LIMIT 5;",
    "Ventas con su cliente (JOIN)": (
        "SELECT v.id_venta, v.fecha, c.nombre AS cliente, v.estado\n"
        "  FROM venta v\n  JOIN cliente c ON c.id_cliente = v.id_cliente\n ORDER BY v.fecha DESC;"),
    "Insertar cliente": (
        "INSERT INTO cliente (tipo_doc, documento, nombre, tipo, email, ciudad)\n"
        "VALUES ('CC', '1122334455', 'Cliente Consola', 'PERSONA', 'consola@correo.com', 'Barranquilla');"),
    "Actualizar precio": "UPDATE producto SET precio = precio * 1.05 WHERE codigo = 'PER-001';",
    "Eliminar cliente sin compras": "DELETE FROM cliente WHERE documento = '1122334455';",
    "Error: documento duplicado": (
        "INSERT INTO cliente (tipo_doc, documento, nombre, tipo, ciudad)\n"
        "VALUES ('CC', '1045678912', 'Duplicado', 'PERSONA', 'Soledad');"),
    "Error: borrar cliente con ventas": "DELETE FROM cliente WHERE id_cliente = 1;",
    "Error: NIT con DV equivocado (CHECK)": (
        "INSERT INTO cliente (tipo_doc, documento, nombre, tipo, ciudad)\n"
        "VALUES ('NIT', '900111222-5', 'Empresa DV malo', 'EMPRESA', 'Soledad');"),
    "Error: cédula con letras (CHECK)": (
        "INSERT INTO cliente (tipo_doc, documento, nombre, tipo, ciudad)\n"
        "VALUES ('CC', '10A5678', 'Cédula inválida', 'PERSONA', 'Soledad');"),
    "Error: precio negativo (CHECK)": "UPDATE producto SET precio = -1 WHERE id_producto = 1;",
    "Error: categoría inexistente (FK)": (
        "INSERT INTO producto (codigo, nombre, id_categoria, precio, stock)\n"
        "VALUES ('X-001', 'Huérfano', 99, 1000, 1);"),
}


def cargar_ejemplo():
    sql = EJEMPLOS_SQL[st.session_state.ejemplo_sql]
    if sql:
        st.session_state.consola_sql = sql


def pagina_consola():
    izq, der = st.columns([3, 1])
    with der:
        subtitulo("Tablas")
        tablas = db.consultar("SELECT name FROM sqlite_master WHERE type = 'table' "
                              "AND name NOT LIKE 'sqlite_%' ORDER BY name", registrar=False)["name"]
        lineas = []
        for t in tablas:
            n = db.valor(f'SELECT COUNT(*) FROM "{t}"')
            lineas.append(f'<span class="k">{esc(t.ljust(14))}</span><span class="v">{n:>4}</span>')
        lineas.append('<span class="d">v_venta_resumen (vista)</span>')
        pre("\n".join(lineas))
    with izq:
        st.selectbox("Ejemplos", list(EJEMPLOS_SQL), key="ejemplo_sql", on_change=cargar_ejemplo)
        script = st.text_area("sqlite>", key="consola_sql", height=150,
                              placeholder="Escriba una o varias sentencias SQL terminadas en ;")
        b1, b2, _ = st.columns([1, 1, 3])
        ejecutar = b1.button("< Ejecutar >", type="primary", width="stretch")
        b2.button("< Limpiar >", width="stretch", on_click=lambda: st.session_state.update(consola_sql=""))
        ayuda("Todas las sentencias se ejecutan en una sola transacción: si una falla, se hace ROLLBACK de todas.")

    if ejecutar and script.strip():
        try:
            resultados = db.ejecutar_script(script)
        except DBError as e:
            mensaje("err", str(e))
            return
        st.session_state.historial_sql.append(script.strip())
        for sentencia, df, filas in resultados:
            pre(f'<span class="g">sqlite&gt;</span> {esc(" ".join(sentencia.split()))}')
            if df is not None:
                tabla(df)
                ayuda(f"{filas} fila(s)")
            else:
                mensaje("ok", f"Ejecutada. Filas afectadas: {max(filas, 0)}")

    if st.session_state.historial_sql:
        with st.expander(f"Historial de la sesión ({len(st.session_state.historial_sql)})"):
            for s in reversed(st.session_state.historial_sql[-15:]):
                st.code(s, language="sql")


# ---------------------------------------------------------------- modelo E-R
ENTIDADES_ER = {
    "CATEGORIA": ["PK id_categoria", "   nombre        UQ", "   descripcion"],
    "PRODUCTO": ["PK id_producto", "   codigo        UQ", "   nombre", "FK id_categoria", "   precio        CK",
                 "   stock         CK", "   stock_minimo  CK", "   activo        CK"],
    "CLIENTE": ["PK id_cliente", "   tipo_doc      CK", "   documento     UQ", "   nombre", "   tipo          CK",
                "   email      UQ,CK", "   telefono", "   ciudad", "   fecha_registro"],
    "VENTA": ["PK id_venta", "   fecha", "FK id_cliente", "FK id_vendedor", "   metodo_pago   CK", "   estado        CK"],
    "DETALLE_VENTA": ["PK FK id_venta", "PK FK id_producto", "   cantidad      CK", "   precio_unitario",
                      "   descuento     CK"],
    "VENDEDOR": ["PK id_vendedor", "   documento     UQ", "   nombre", "   email         UQ", "   comision      CK",
                 "   activo        CK"],
}


def diagrama_er():
    """Dibuja el diagrama entidad-relación con caracteres de caja."""
    ancho, alto = 92, 37
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

    def vertical(x, y1, y2, muchos_abajo=True):  # une la caja de arriba (y1-1) con la de abajo (y2+1)
        poner(x, y1 - 1, "┬")
        poner(x, y2 + 1, "┴")
        for y in range(y1, y2 + 1):
            poner(x, y, "│")
        poner(x, y2 if muchos_abajo else y1, "Λ" if muchos_abajo else "V")
        poner(x + 2, y1, "1" if muchos_abajo else "N")
        poner(x + 2, y2, "N" if muchos_abajo else "1")

    caja(33, 0, "CATEGORIA")
    caja(66, 0, "PRODUCTO")
    caja(0, 14, "CLIENTE")
    caja(33, 14, "VENTA")
    caja(66, 14, "DETALLE_VENTA")
    caja(33, 26, "VENDEDOR")
    horizontal(58, 66, 3)    # CATEGORIA 1 ──< N PRODUCTO
    horizontal(25, 33, 17)   # CLIENTE   1 ──< N VENTA
    horizontal(58, 66, 17)   # VENTA     1 ──< N DETALLE_VENTA
    vertical(78, 12, 13)     # PRODUCTO  1 ──< N DETALLE_VENTA
    vertical(45, 24, 25, muchos_abajo=False)  # VENDEDOR 1 ──< N VENTA
    return "\n".join("".join(f).rstrip() for f in lienzo).rstrip()


def pagina_modelo():
    accion = submenu("sub_modelo", ["Diagrama E-R", "Diccionario de datos", "Script DDL"])
    if accion == "Diagrama E-R":
        pre(esc(diagrama_er()))
        ayuda("PK clave primaria · FK clave foránea · UQ único · CK restricción CHECK · "
              "1 ──< N relación uno a muchos. DETALLE_VENTA resuelve la relación N:M entre VENTA y PRODUCTO.")
    elif accion == "Diccionario de datos":
        tablas = ["categoria", "producto", "cliente", "vendedor", "venta", "detalle_venta"]
        # Opciones fijas: un selectbox deja escribir para filtrar y parece un campo editable
        t = st.radio("Tabla", tablas, horizontal=True, key="dic_tabla")
        subtitulo("Columnas")
        columnas = db.consultar(f"PRAGMA table_info({t})", registrar=False)
        columnas = columnas.rename(columns={"name": "columna", "type": "tipo", "notnull": "not_null",
                                            "dflt_value": "defecto", "pk": "pk"}).drop(columns=["cid"])
        tabla(columnas)
        subtitulo("Claves foráneas")
        fks = db.consultar(f"PRAGMA foreign_key_list({t})", registrar=False)
        if fks.empty:
            ayuda("Esta tabla no tiene claves foráneas.")
        else:
            tabla(fks[["from", "table", "to", "on_update", "on_delete"]]
                  .rename(columns={"from": "columna", "table": "referencia", "to": "columna_ref"}))
        subtitulo("Índices y triggers")
        tabla(db.consultar("SELECT type AS tipo, name AS nombre FROM sqlite_master "
                           "WHERE tbl_name = ? AND type IN ('index', 'trigger') ORDER BY type, name",
                           (t,), registrar=False))
    else:
        st.code((SQL_DIR / "schema.sql").read_text(encoding="utf-8"), language="sql")


def pagina_sistema():
    izq, der = st.columns([1, 1])
    with izq:
        subtitulo("Acerca de")
        pre("\n".join([
            f'<span class="k">Proyecto  :</span> {esc(CURSO)}',
            f'<span class="k">Empresa   :</span> {esc(EMPRESA)}',
            '<span class="k">Tecnología:</span> Python · Streamlit · SQLite · pandas',
            '<span class="k">Integrantes:</span>',
        ] + [f'   <span class="v">- {esc(n)}</span>' for n in INTEGRANTES]))
    with der:
        subtitulo("Base de datos")
        if DB_PATH.exists():
            st.download_button("< Descargar kstore.db >", DB_PATH.read_bytes(), file_name="kstore.db",
                               width="stretch")
        for nombre in ["schema.sql", "seed.sql", "consultas.sql", "ejemplos_dml.sql"]:
            st.download_button(f"< Descargar {nombre} >", (SQL_DIR / nombre).read_bytes(), file_name=nombre,
                               width="stretch", key=f"dl_{nombre}")
        subtitulo("Reiniciar")
        ayuda("Borra todo y vuelve a cargar los datos de ejemplo (schema.sql + seed.sql).")
        confirmar = st.checkbox("Confirmo reiniciar la base de datos", key="conf_reset")
        if st.button("< Reiniciar base de datos >", disabled=not confirmar, width="stretch"):
            db.reiniciar()
            st.session_state.carrito = []
            del st.session_state["conf_reset"]
            avisar_luego("ok", "Base de datos reiniciada con los datos de ejemplo.")
            st.rerun()
        if st.button("< Limpiar mensajes >", width="stretch"):
            st.session_state.log.clear()
            st.rerun()


# ---------------------------------------------------------------- estructura
MENU = [
    ("inicio", "1 Inicio / Status", pagina_inicio),
    ("clientes", "2 Clientes  --->", lambda: pagina_crud("clientes")),
    ("productos", "3 Productos  --->", lambda: pagina_crud("productos")),
    ("categorias", "4 Categorías  --->", lambda: pagina_crud("categorias")),
    ("vendedores", "5 Vendedores  --->", lambda: pagina_crud("vendedores")),
    ("ventas", "6 Ventas  --->", pagina_ventas),
    ("reportes", "7 Reportes SQL  --->", pagina_reportes),
    ("consola", "8 Consola SQL", pagina_consola),
    ("modelo", "9 Modelo E-R  --->", pagina_modelo),
    ("sistema", "0 Sistema", pagina_sistema),
]


def panel_mensajes():
    lineas = []
    for hora, estado, texto in reversed(st.session_state.log[-60:]):
        clase = {"OK": "ok", "ERR": "err", "TX": "tx"}[estado]
        lineas.append(f'<span class="t">[{hora}]</span> <span class="{clase}">{estado:<3}</span> {esc(texto)}')
    if not lineas:
        lineas.append('<span class="t">Sin actividad. Aquí aparece cada sentencia SQL que ejecuta el sistema.</span>')
    st.html(f'<div class="tb-log">{"<br>".join(lineas)}</div>')


def main():
    st.markdown(CSS, unsafe_allow_html=True)
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M")
    st.markdown(f'<div class="tb-top"><span>kstore.db ── {esc(EMPRESA)} ── Sistema de Gestión de Ventas'
                f' v{VERSION}</span><span>{ahora}</span></div>', unsafe_allow_html=True)

    col_menu, col_main = st.columns([1, 4])
    with col_menu:
        with st.container(key="caja_menu"):
            titulo("Menú")
            with st.container(key="menu"):
                for clave, etiqueta, _ in MENU:
                    activo = st.session_state.menu == clave
                    if st.button(etiqueta, key=f"m_{clave}", type="primary" if activo else "secondary",
                                 width="stretch"):
                        st.session_state.menu = clave
                        st.rerun()
            ayuda("Teclas: 0-9 elegir · ↑↓ mover · Enter abrir · Esc inicio")

    clave_actual = st.session_state.menu
    etiqueta, pagina = next((e, p) for c, e, p in MENU if c == clave_actual)
    with col_main:
        with st.container(key="caja_main"):
            titulo(etiqueta[2:].replace("--->", "").strip())
            mostrar_aviso()
            pagina()

    with st.container(key="caja_log"):
        titulo("Mensajes  ·  bitácora SQL")
        panel_mensajes()

    st.markdown(
        '<div class="tb-bar"><span><b>0-9</b> Menú  <b>↑↓</b> Navegar  <b>Enter</b> Seleccionar  '
        f'<b>Esc</b> Inicio</span><span>SQLite {sqlite3.sqlite_version} · {esc(CURSO)}</span></div>',
        unsafe_allow_html=True)
    components.html(ATAJOS_JS, height=0)


main()
