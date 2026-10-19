-- =====================================================================
--  KStore S.A.S. - Sistema de Pedidos
--  Laboratorio 01 - Bases de Datos
--  Script de creación (DDL) para SQLite 3
-- =====================================================================
--  Enunciado: una empresa vende productos a varios clientes. Un cliente
--  puede comprar varios productos y un producto puede ser comprado por
--  varios clientes. Cada producto lo suministra un solo proveedor, y un
--  proveedor puede suministrar varios productos.
--
--  Modelo:
--    PROVEEDOR (1) ──< (N) PRODUCTO
--    CLIENTE   (1) ──< (N) PEDIDO
--    PEDIDO    (1) ──< (N) DETALLE_PEDIDO >── (1) PRODUCTO
--  DETALLE_PEDIDO resuelve la relación muchos a muchos entre los pedidos
--  de los clientes y los productos.
-- =====================================================================

PRAGMA foreign_keys = ON;

-- Se eliminan en orden inverso a las dependencias (hijas primero)
DROP VIEW  IF EXISTS v_pedido_resumen;
DROP TABLE IF EXISTS detalle_pedido;
DROP TABLE IF EXISTS pedido;
DROP TABLE IF EXISTS producto;
DROP TABLE IF EXISTS proveedor;
DROP TABLE IF EXISTS cliente;

-- ---------------------------------------------------------------------
-- PROVEEDOR: nit, nombre y dirección
-- El NIT se guarda como 900123456-8: 9 dígitos, guion y dígito de
-- verificación (DV) calculado con el algoritmo módulo 11 de la DIAN.
-- ---------------------------------------------------------------------
CREATE TABLE proveedor (
    id_proveedor  INTEGER PRIMARY KEY AUTOINCREMENT,
    nit           TEXT    NOT NULL,
    nombre        TEXT    NOT NULL,
    direccion     TEXT    NOT NULL,
    CONSTRAINT uq_proveedor_nit UNIQUE (nit),
    CONSTRAINT ck_proveedor_nit CHECK (nit GLOB '[89][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]-[0-9]'),
    --   suma = d1*41 + d2*37 + d3*29 + d4*23 + d5*19 + d6*17 + d7*13 + d8*7 + d9*3
    --   DV   = residuo si (suma % 11) es 0 o 1; si no, 11 - residuo
    CONSTRAINT ck_proveedor_nit_dv CHECK (
        CAST(substr(nit, 11, 1) AS INTEGER) =
        CASE WHEN (41 * CAST(substr(nit, 1, 1) AS INTEGER) + 37 * CAST(substr(nit, 2, 1) AS INTEGER)
                 + 29 * CAST(substr(nit, 3, 1) AS INTEGER) + 23 * CAST(substr(nit, 4, 1) AS INTEGER)
                 + 19 * CAST(substr(nit, 5, 1) AS INTEGER) + 17 * CAST(substr(nit, 6, 1) AS INTEGER)
                 + 13 * CAST(substr(nit, 7, 1) AS INTEGER) +  7 * CAST(substr(nit, 8, 1) AS INTEGER)
                 +  3 * CAST(substr(nit, 9, 1) AS INTEGER)) % 11 < 2
             THEN (41 * CAST(substr(nit, 1, 1) AS INTEGER) + 37 * CAST(substr(nit, 2, 1) AS INTEGER)
                 + 29 * CAST(substr(nit, 3, 1) AS INTEGER) + 23 * CAST(substr(nit, 4, 1) AS INTEGER)
                 + 19 * CAST(substr(nit, 5, 1) AS INTEGER) + 17 * CAST(substr(nit, 6, 1) AS INTEGER)
                 + 13 * CAST(substr(nit, 7, 1) AS INTEGER) +  7 * CAST(substr(nit, 8, 1) AS INTEGER)
                 +  3 * CAST(substr(nit, 9, 1) AS INTEGER)) % 11
             ELSE 11 - (41 * CAST(substr(nit, 1, 1) AS INTEGER) + 37 * CAST(substr(nit, 2, 1) AS INTEGER)
                 + 29 * CAST(substr(nit, 3, 1) AS INTEGER) + 23 * CAST(substr(nit, 4, 1) AS INTEGER)
                 + 19 * CAST(substr(nit, 5, 1) AS INTEGER) + 17 * CAST(substr(nit, 6, 1) AS INTEGER)
                 + 13 * CAST(substr(nit, 7, 1) AS INTEGER) +  7 * CAST(substr(nit, 8, 1) AS INTEGER)
                 +  3 * CAST(substr(nit, 9, 1) AS INTEGER)) % 11
        END)
);

-- ---------------------------------------------------------------------
-- CLIENTE: identificación, nombre, apellidos, dirección y fecha de nacimiento
-- La identificación sigue el formato colombiano y se guarda sin puntos:
--   CC : cédula de ciudadanía, 6 a 10 dígitos   ej. 1045678912
--   CE : cédula de extranjería, 6 a 7 dígitos   ej. 845123
-- ---------------------------------------------------------------------
CREATE TABLE cliente (
    id_cliente        INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo_doc          TEXT    NOT NULL DEFAULT 'CC',
    identificacion    TEXT    NOT NULL,
    nombre            TEXT    NOT NULL,
    apellidos         TEXT    NOT NULL,
    direccion         TEXT    NOT NULL,
    fecha_nacimiento  TEXT    NOT NULL,
    CONSTRAINT uq_cliente_identificacion UNIQUE (identificacion),
    CONSTRAINT ck_cliente_tipo_doc       CHECK (tipo_doc IN ('CC', 'CE')),
    CONSTRAINT ck_cliente_identificacion CHECK (
            identificacion NOT GLOB '*[^0-9]*' AND identificacion NOT GLOB '0*'
        AND ((tipo_doc = 'CC' AND length(identificacion) BETWEEN 6 AND 10)
          OR (tipo_doc = 'CE' AND length(identificacion) BETWEEN 6 AND 7))),
    -- Fecha real en formato AAAA-MM-DD y posterior a 1900. date(x, '+0 days')
    -- normaliza fechas imposibles (2001-02-30 -> 2001-03-02), así que no coinciden.
    CONSTRAINT ck_cliente_fecha_nac CHECK (fecha_nacimiento = date(fecha_nacimiento, '+0 days')
                                           AND fecha_nacimiento >= '1900-01-01')
);

-- ---------------------------------------------------------------------
-- PRODUCTO: código, nombre y precio unitario. Lo suministra UN proveedor.
-- ---------------------------------------------------------------------
CREATE TABLE producto (
    id_producto      INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo           TEXT    NOT NULL,
    nombre           TEXT    NOT NULL,
    precio_unitario  REAL    NOT NULL,
    id_proveedor     INTEGER NOT NULL,
    CONSTRAINT uq_producto_codigo UNIQUE (codigo),
    CONSTRAINT ck_producto_precio CHECK (precio_unitario > 0),
    CONSTRAINT fk_producto_proveedor FOREIGN KEY (id_proveedor)
        REFERENCES proveedor (id_proveedor)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

-- ---------------------------------------------------------------------
-- PEDIDO: encabezado de cada compra que hace un cliente
-- ---------------------------------------------------------------------
CREATE TABLE pedido (
    id_pedido   INTEGER PRIMARY KEY AUTOINCREMENT,
    id_cliente  INTEGER NOT NULL,
    fecha       TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    CONSTRAINT fk_pedido_cliente FOREIGN KEY (id_cliente)
        REFERENCES cliente (id_cliente)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

-- ---------------------------------------------------------------------
-- DETALLE_PEDIDO: productos de cada pedido (tabla intermedia N:M)
-- precio_compra guarda el precio del momento del pedido, así un cambio de
-- precio en PRODUCTO no altera los pedidos ya hechos.
-- ---------------------------------------------------------------------
CREATE TABLE detalle_pedido (
    id_pedido      INTEGER NOT NULL,
    id_producto    INTEGER NOT NULL,
    cantidad       INTEGER NOT NULL,
    precio_compra  REAL    NOT NULL,
    CONSTRAINT pk_detalle_pedido PRIMARY KEY (id_pedido, id_producto),
    CONSTRAINT ck_detalle_cantidad CHECK (cantidad > 0),
    CONSTRAINT ck_detalle_precio   CHECK (precio_compra > 0),
    CONSTRAINT fk_detalle_pedido FOREIGN KEY (id_pedido)
        REFERENCES pedido (id_pedido)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_detalle_producto FOREIGN KEY (id_producto)
        REFERENCES producto (id_producto)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

-- ---------------------------------------------------------------------
-- Índices sobre las claves foráneas
-- ---------------------------------------------------------------------
CREATE INDEX idx_producto_proveedor ON producto (id_proveedor);
CREATE INDEX idx_pedido_cliente     ON pedido (id_cliente);
CREATE INDEX idx_detalle_producto   ON detalle_pedido (id_producto);

-- ---------------------------------------------------------------------
-- Vista: total de cada pedido
-- ---------------------------------------------------------------------
CREATE VIEW v_pedido_resumen AS
SELECT pe.id_pedido,
       pe.fecha,
       pe.id_cliente,
       c.nombre || ' ' || c.apellidos                  AS cliente,
       COUNT(d.id_producto)                            AS productos,
       COALESCE(SUM(d.cantidad), 0)                    AS unidades,
       COALESCE(SUM(d.cantidad * d.precio_compra), 0)  AS total
  FROM pedido pe
  JOIN cliente c ON c.id_cliente = pe.id_cliente
  LEFT JOIN detalle_pedido d ON d.id_pedido = pe.id_pedido
 GROUP BY pe.id_pedido;
