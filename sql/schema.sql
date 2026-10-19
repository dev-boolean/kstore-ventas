-- =====================================================================
--  KStore S.A.S. - Sistema de Gestión de Ventas
--  Laboratorio 01 - Bases de Datos
--  Script de creación (DDL) para SQLite 3
-- =====================================================================
--  Modelo:
--    CATEGORIA (1) ──< (N) PRODUCTO
--    CLIENTE   (1) ──< (N) VENTA
--    VENDEDOR  (1) ──< (N) VENTA
--    VENTA     (1) ──< (N) DETALLE_VENTA >── (1) PRODUCTO
--  DETALLE_VENTA resuelve la relación muchos a muchos VENTA <-> PRODUCTO.
-- =====================================================================

PRAGMA foreign_keys = ON;

-- Se eliminan en orden inverso a las dependencias (hijas primero)
DROP VIEW    IF EXISTS v_venta_resumen;
DROP TABLE   IF EXISTS detalle_venta;
DROP TABLE   IF EXISTS venta;
DROP TABLE   IF EXISTS producto;
DROP TABLE   IF EXISTS categoria;
DROP TABLE   IF EXISTS cliente;
DROP TABLE   IF EXISTS vendedor;

-- ---------------------------------------------------------------------
-- CATEGORIA: agrupa los productos del catálogo
-- ---------------------------------------------------------------------
CREATE TABLE categoria (
    id_categoria  INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre        TEXT    NOT NULL,
    descripcion   TEXT,
    CONSTRAINT uq_categoria_nombre UNIQUE (nombre)
);

-- ---------------------------------------------------------------------
-- PRODUCTO: catálogo de artículos que vende la empresa
-- ---------------------------------------------------------------------
CREATE TABLE producto (
    id_producto   INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo        TEXT    NOT NULL,
    nombre        TEXT    NOT NULL,
    id_categoria  INTEGER NOT NULL,
    precio        REAL    NOT NULL,
    stock         INTEGER NOT NULL DEFAULT 0,
    stock_minimo  INTEGER NOT NULL DEFAULT 5,
    activo        INTEGER NOT NULL DEFAULT 1,
    CONSTRAINT uq_producto_codigo   UNIQUE (codigo),
    CONSTRAINT ck_producto_precio   CHECK (precio > 0),
    CONSTRAINT ck_producto_stock    CHECK (stock >= 0),
    CONSTRAINT ck_producto_stockmin CHECK (stock_minimo >= 0),
    CONSTRAINT ck_producto_activo   CHECK (activo IN (0, 1)),
    CONSTRAINT fk_producto_categoria FOREIGN KEY (id_categoria)
        REFERENCES categoria (id_categoria)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

-- ---------------------------------------------------------------------
-- CLIENTE: personas naturales o empresas que compran
-- ---------------------------------------------------------------------
CREATE TABLE cliente (
    id_cliente     INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo_doc       TEXT    NOT NULL,
    documento      TEXT    NOT NULL,
    nombre         TEXT    NOT NULL,
    tipo           TEXT    NOT NULL DEFAULT 'PERSONA',
    email          TEXT,
    telefono       TEXT,
    ciudad         TEXT    NOT NULL,
    fecha_registro TEXT    NOT NULL DEFAULT (date('now', 'localtime')),
    CONSTRAINT uq_cliente_documento UNIQUE (documento),
    CONSTRAINT uq_cliente_email     UNIQUE (email),
    CONSTRAINT ck_cliente_tipo_doc  CHECK (tipo_doc IN ('CC', 'NIT', 'CE')),
    CONSTRAINT ck_cliente_tipo      CHECK (tipo IN ('PERSONA', 'EMPRESA')),
    CONSTRAINT ck_cliente_email     CHECK (email IS NULL OR email LIKE '%_@_%._%'),
    -- Las empresas se identifican con NIT y las personas con CC o CE
    CONSTRAINT ck_cliente_doc_tipo  CHECK ((tipo = 'EMPRESA' AND tipo_doc = 'NIT')
                                        OR (tipo = 'PERSONA' AND tipo_doc IN ('CC', 'CE'))),
    -- Formato colombiano (se guarda sin puntos):
    --   CC : 6 a 10 dígitos, sin cero inicial       ej. 1045678912
    --   CE : 6 a 7 dígitos, sin cero inicial        ej. 845123
    --   NIT: 9 dígitos que empiezan por 8 o 9, guion y dígito de verificación  ej. 900123456-8
    CONSTRAINT ck_cliente_documento CHECK (
           (tipo_doc = 'CC'  AND documento NOT GLOB '*[^0-9]*' AND documento NOT GLOB '0*'
                             AND length(documento) BETWEEN 6 AND 10)
        OR (tipo_doc = 'CE'  AND documento NOT GLOB '*[^0-9]*' AND documento NOT GLOB '0*'
                             AND length(documento) BETWEEN 6 AND 7)
        OR (tipo_doc = 'NIT' AND documento GLOB '[89][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]-[0-9]')),
    -- Dígito de verificación del NIT (algoritmo módulo 11 de la DIAN):
    --   suma = d1*41 + d2*37 + d3*29 + d4*23 + d5*19 + d6*17 + d7*13 + d8*7 + d9*3
    --   DV   = residuo si (suma % 11) es 0 o 1; si no, 11 - residuo
    CONSTRAINT ck_cliente_nit_dv CHECK (
        tipo_doc <> 'NIT'
        OR CAST(substr(documento, 11, 1) AS INTEGER) =
           CASE WHEN (41 * CAST(substr(documento, 1, 1) AS INTEGER) + 37 * CAST(substr(documento, 2, 1) AS INTEGER)
                      + 29 * CAST(substr(documento, 3, 1) AS INTEGER) + 23 * CAST(substr(documento, 4, 1) AS INTEGER)
                      + 19 * CAST(substr(documento, 5, 1) AS INTEGER) + 17 * CAST(substr(documento, 6, 1) AS INTEGER)
                      + 13 * CAST(substr(documento, 7, 1) AS INTEGER) +  7 * CAST(substr(documento, 8, 1) AS INTEGER)
                      +  3 * CAST(substr(documento, 9, 1) AS INTEGER)) % 11 < 2
                THEN (41 * CAST(substr(documento, 1, 1) AS INTEGER) + 37 * CAST(substr(documento, 2, 1) AS INTEGER)
                      + 29 * CAST(substr(documento, 3, 1) AS INTEGER) + 23 * CAST(substr(documento, 4, 1) AS INTEGER)
                      + 19 * CAST(substr(documento, 5, 1) AS INTEGER) + 17 * CAST(substr(documento, 6, 1) AS INTEGER)
                      + 13 * CAST(substr(documento, 7, 1) AS INTEGER) +  7 * CAST(substr(documento, 8, 1) AS INTEGER)
                      +  3 * CAST(substr(documento, 9, 1) AS INTEGER)) % 11
                ELSE 11 - (41 * CAST(substr(documento, 1, 1) AS INTEGER) + 37 * CAST(substr(documento, 2, 1) AS INTEGER)
                      + 29 * CAST(substr(documento, 3, 1) AS INTEGER) + 23 * CAST(substr(documento, 4, 1) AS INTEGER)
                      + 19 * CAST(substr(documento, 5, 1) AS INTEGER) + 17 * CAST(substr(documento, 6, 1) AS INTEGER)
                      + 13 * CAST(substr(documento, 7, 1) AS INTEGER) +  7 * CAST(substr(documento, 8, 1) AS INTEGER)
                      +  3 * CAST(substr(documento, 9, 1) AS INTEGER)) % 11
           END)
);

-- ---------------------------------------------------------------------
-- VENDEDOR: empleados que registran las ventas
-- ---------------------------------------------------------------------
CREATE TABLE vendedor (
    id_vendedor  INTEGER PRIMARY KEY AUTOINCREMENT,
    documento    TEXT    NOT NULL,
    nombre       TEXT    NOT NULL,
    email        TEXT,
    comision     REAL    NOT NULL DEFAULT 0.02,
    activo       INTEGER NOT NULL DEFAULT 1,
    CONSTRAINT uq_vendedor_documento UNIQUE (documento),
    -- Cédula de ciudadanía: 6 a 10 dígitos, sin cero inicial
    CONSTRAINT ck_vendedor_documento CHECK (documento NOT GLOB '*[^0-9]*' AND documento NOT GLOB '0*'
                                            AND length(documento) BETWEEN 6 AND 10),
    CONSTRAINT uq_vendedor_email     UNIQUE (email),
    CONSTRAINT ck_vendedor_comision  CHECK (comision BETWEEN 0 AND 0.20),
    CONSTRAINT ck_vendedor_activo    CHECK (activo IN (0, 1))
);

-- ---------------------------------------------------------------------
-- VENTA: encabezado de la factura
-- ---------------------------------------------------------------------
CREATE TABLE venta (
    id_venta     INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha        TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    id_cliente   INTEGER NOT NULL,
    id_vendedor  INTEGER NOT NULL,
    metodo_pago  TEXT    NOT NULL,
    estado       TEXT    NOT NULL DEFAULT 'PAGADA',
    CONSTRAINT ck_venta_metodo CHECK (metodo_pago IN ('EFECTIVO', 'TARJETA', 'TRANSFERENCIA', 'CREDITO')),
    CONSTRAINT ck_venta_estado CHECK (estado IN ('PAGADA', 'PENDIENTE', 'ANULADA')),
    CONSTRAINT fk_venta_cliente FOREIGN KEY (id_cliente)
        REFERENCES cliente (id_cliente)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_venta_vendedor FOREIGN KEY (id_vendedor)
        REFERENCES vendedor (id_vendedor)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

-- ---------------------------------------------------------------------
-- DETALLE_VENTA: productos incluidos en cada venta (tabla intermedia N:M)
-- precio_unitario guarda el precio del momento de la venta, así un cambio
-- de precio en PRODUCTO no altera las facturas ya emitidas.
-- ---------------------------------------------------------------------
CREATE TABLE detalle_venta (
    id_venta         INTEGER NOT NULL,
    id_producto      INTEGER NOT NULL,
    cantidad         INTEGER NOT NULL,
    precio_unitario  REAL    NOT NULL,
    descuento        REAL    NOT NULL DEFAULT 0,
    CONSTRAINT pk_detalle_venta PRIMARY KEY (id_venta, id_producto),
    CONSTRAINT ck_detalle_cantidad  CHECK (cantidad > 0),
    CONSTRAINT ck_detalle_precio    CHECK (precio_unitario > 0),
    CONSTRAINT ck_detalle_descuento CHECK (descuento BETWEEN 0 AND 0.50),
    CONSTRAINT fk_detalle_venta FOREIGN KEY (id_venta)
        REFERENCES venta (id_venta)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_detalle_producto FOREIGN KEY (id_producto)
        REFERENCES producto (id_producto)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

-- ---------------------------------------------------------------------
-- Índices para acelerar las búsquedas por claves foráneas y fechas
-- ---------------------------------------------------------------------
CREATE INDEX idx_producto_categoria ON producto (id_categoria);
CREATE INDEX idx_venta_cliente      ON venta (id_cliente);
CREATE INDEX idx_venta_vendedor     ON venta (id_vendedor);
CREATE INDEX idx_venta_fecha        ON venta (fecha);
CREATE INDEX idx_detalle_producto   ON detalle_venta (id_producto);

-- ---------------------------------------------------------------------
-- Disparadores (triggers) de integridad de negocio
-- ---------------------------------------------------------------------

-- No se puede vender más de lo que hay en inventario
CREATE TRIGGER trg_detalle_valida_stock
BEFORE INSERT ON detalle_venta
WHEN (SELECT stock FROM producto WHERE id_producto = NEW.id_producto) < NEW.cantidad
BEGIN
    SELECT RAISE(ABORT, 'Stock insuficiente para el producto solicitado');
END;

-- No se pueden agregar productos a una venta anulada
CREATE TRIGGER trg_detalle_valida_venta
BEFORE INSERT ON detalle_venta
WHEN (SELECT estado FROM venta WHERE id_venta = NEW.id_venta) = 'ANULADA'
BEGIN
    SELECT RAISE(ABORT, 'No se pueden agregar productos a una venta anulada');
END;

-- Al vender, se descuenta el inventario
CREATE TRIGGER trg_detalle_descuenta_stock
AFTER INSERT ON detalle_venta
BEGIN
    UPDATE producto
       SET stock = stock - NEW.cantidad
     WHERE id_producto = NEW.id_producto;
END;

-- Al anular una venta, el inventario se devuelve
CREATE TRIGGER trg_venta_anular
AFTER UPDATE OF estado ON venta
WHEN NEW.estado = 'ANULADA' AND OLD.estado <> 'ANULADA'
BEGIN
    UPDATE producto
       SET stock = stock + (SELECT d.cantidad FROM detalle_venta d
                             WHERE d.id_venta = NEW.id_venta
                               AND d.id_producto = producto.id_producto)
     WHERE id_producto IN (SELECT id_producto FROM detalle_venta
                            WHERE id_venta = NEW.id_venta);
END;

-- Una venta anulada no puede volver a activarse
CREATE TRIGGER trg_venta_no_reactivar
BEFORE UPDATE OF estado ON venta
WHEN OLD.estado = 'ANULADA' AND NEW.estado <> 'ANULADA'
BEGIN
    SELECT RAISE(ABORT, 'Una venta anulada no se puede reactivar');
END;

-- Al eliminar una venta no anulada, el inventario se devuelve
-- (sus detalles se borran solos por ON DELETE CASCADE)
CREATE TRIGGER trg_venta_eliminar
BEFORE DELETE ON venta
WHEN OLD.estado <> 'ANULADA'
BEGIN
    UPDATE producto
       SET stock = stock + (SELECT d.cantidad FROM detalle_venta d
                             WHERE d.id_venta = OLD.id_venta
                               AND d.id_producto = producto.id_producto)
     WHERE id_producto IN (SELECT id_producto FROM detalle_venta
                            WHERE id_venta = OLD.id_venta);
END;

-- ---------------------------------------------------------------------
-- Vista: totales de cada venta (subtotal, IVA 19 % y total)
-- ---------------------------------------------------------------------
CREATE VIEW v_venta_resumen AS
SELECT v.id_venta,
       v.fecha,
       v.id_cliente,
       c.nombre       AS cliente,
       v.id_vendedor,
       ve.nombre      AS vendedor,
       v.metodo_pago,
       v.estado,
       COUNT(d.id_producto)                                                  AS items,
       ROUND(COALESCE(SUM(d.cantidad * d.precio_unitario * (1 - d.descuento)), 0), 0)        AS subtotal,
       ROUND(COALESCE(SUM(d.cantidad * d.precio_unitario * (1 - d.descuento)), 0) * 0.19, 0) AS iva,
       ROUND(COALESCE(SUM(d.cantidad * d.precio_unitario * (1 - d.descuento)), 0) * 1.19, 0) AS total
  FROM venta v
  JOIN cliente  c  ON c.id_cliente   = v.id_cliente
  JOIN vendedor ve ON ve.id_vendedor = v.id_vendedor
  LEFT JOIN detalle_venta d ON d.id_venta = v.id_venta
 GROUP BY v.id_venta;
