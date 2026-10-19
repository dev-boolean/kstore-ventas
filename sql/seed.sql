-- =====================================================================
--  KStore S.A.S. - Datos de ejemplo (DML)
--  Se ejecuta después de schema.sql. Los triggers descuentan el stock
--  automáticamente al insertar cada detalle de venta.
--  Todos los nombres, documentos y correos son ficticios.
-- =====================================================================

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------------
-- Categorías
-- ---------------------------------------------------------------------
INSERT INTO categoria (nombre, descripcion) VALUES
 ('Portátiles',  'Computadores portátiles para hogar, estudio y oficina'),
 ('Periféricos', 'Mouse, teclados, monitores, cámaras y audio'),
 ('Componentes', 'Partes internas: memorias, discos, fuentes y tarjetas'),
 ('Redes',       'Routers, switches y cableado estructurado'),
 ('Gaming',      'Accesorios y mobiliario para videojuegos');

-- ---------------------------------------------------------------------
-- Productos (precios en pesos colombianos, antes de IVA)
-- ---------------------------------------------------------------------
INSERT INTO producto (codigo, nombre, id_categoria, precio, stock, stock_minimo) VALUES
 ('POR-001', 'Portátil Lenovo IdeaPad 3 Ryzen 5',   1, 2799000, 12, 3),
 ('POR-002', 'Portátil HP 15 Core i5 16GB',         1, 3199000, 10, 3),
 ('POR-003', 'MacBook Air M2 13 pulgadas',          1, 5499000,  5, 2),
 ('POR-004', 'Portátil ASUS VivoBook Core i3',      1, 1899000,  8, 3),
 ('PER-001', 'Mouse Logitech M170 inalámbrico',     2,   45000, 80, 15),
 ('PER-002', 'Teclado Genius KB-110 USB',           2,   32000, 60, 15),
 ('PER-003', 'Monitor Samsung 24" Full HD',         2,  649000, 15, 4),
 ('PER-004', 'Diadema Logitech H390 USB',           2,  159000, 25, 5),
 ('PER-005', 'Cámara web Logitech C920',            2,  329000,  6, 4),
 ('COM-001', 'Memoria RAM Kingston 8GB DDR4',       3,  139000, 40, 10),
 ('COM-002', 'SSD Kingston A400 480GB',             3,  189000, 35, 10),
 ('COM-003', 'Fuente de poder EVGA 600W',           3,  299000, 10, 3),
 ('COM-004', 'Tarjeta gráfica RTX 4060 8GB',        3, 1649000,  4, 2),
 ('RED-001', 'Router TP-Link Archer C6',            4,  199000, 20, 5),
 ('RED-002', 'Switch TP-Link 8 puertos',            4,  119000, 18, 5),
 ('RED-003', 'Cable UTP Cat6 caja 305 m',           4,  489000,  7, 2),
 ('GAM-001', 'Control Xbox inalámbrico',            5,  299000, 14, 4),
 ('GAM-002', 'Silla gamer Cougar Armor',            5, 1199000,  5, 2),
 ('GAM-003', 'Teclado mecánico Redragon Kumara',    5,  189000, 22, 5),
 ('GAM-004', 'Mouse gamer Logitech G203',           5,  119000, 30, 8),
 ('RED-004', 'Adaptador WiFi USB TP-Link',          4,   59000, 25, 5),
 ('GAM-005', 'Audífonos HyperX Cloud Stinger',      5,  229000, 12, 3);

-- ---------------------------------------------------------------------
-- Clientes (personas con CC/CE y empresas con NIT con dígito de verificación válido)
-- ---------------------------------------------------------------------
INSERT INTO cliente (tipo_doc, documento, nombre, tipo, email, telefono, ciudad, fecha_registro) VALUES
 ('CC',  '1045678912',  'Carlos Andrés Pérez',        'PERSONA', 'carlos.perez@correo.com',     '3014567890', 'Barranquilla',    '2026-05-20'),
 ('NIT', '900123456-8', 'Colegio San José',           'EMPRESA', 'compras@colsanjose.edu.co',   '6053456789', 'Barranquilla',    '2026-05-28'),
 ('CC',  '1129876543',  'María Fernanda Gómez',       'PERSONA', 'mafe.gomez@correo.com',       '3156789012', 'Soledad',         '2026-06-10'),
 ('NIT', '901234567-7', 'Cibercafé La Red',           'EMPRESA', 'lared.ciber@correo.com',      '3001234567', 'Malambo',         '2026-06-22'),
 ('CC',  '72145896',    'Jorge Luis Martínez',        'PERSONA', 'jorgel.martinez@correo.com',  '3204567812', 'Barranquilla',    '2026-07-01'),
 ('NIT', '800987654-4', 'Constructora Caribe S.A.S.', 'EMPRESA', 'sistemas@constcaribe.co',     '6053789456', 'Cartagena',       '2026-07-18'),
 ('CC',  '1043987654',  'Laura Valentina Ruiz',       'PERSONA', 'laura.ruiz@correo.com',       '3017894561', 'Puerto Colombia', '2026-08-05'),
 ('NIT', '900555888-1', 'Clínica del Norte IPS',      'EMPRESA', 'ti@clinicadelnorte.co',       '6053321122', 'Barranquilla',    '2026-08-30'),
 ('CE',  '845123',      'Andrea Rossi',               'PERSONA', 'andrea.rossi@correo.com',     '3109998877', 'Santa Marta',     '2026-09-12'),
 ('CC',  '1001234567',  'Kevin David Orozco',         'PERSONA', 'kevin.orozco@correo.com',     '3023456789', 'Barranquilla',    '2026-10-01');

-- ---------------------------------------------------------------------
-- Vendedores
-- ---------------------------------------------------------------------
INSERT INTO vendedor (documento, nombre, email, comision) VALUES
 ('1047111222', 'Ana Lucía Torres',     'ana.torres@kstore.co',  0.030),
 ('1140333444', 'Luis Fernando Castro', 'luis.castro@kstore.co', 0.025),
 ('32789456',   'Diana Marcela Rojas',  'diana.rojas@kstore.co', 0.030);

-- ---------------------------------------------------------------------
-- Ventas (encabezado)
-- ---------------------------------------------------------------------
INSERT INTO venta (fecha, id_cliente, id_vendedor, metodo_pago, estado) VALUES
 ('2026-06-05 10:15:00', 1, 1, 'TARJETA',       'PAGADA'),
 ('2026-06-18 15:40:00', 2, 2, 'TRANSFERENCIA', 'PAGADA'),
 ('2026-07-02 11:05:00', 3, 3, 'EFECTIVO',      'PAGADA'),
 ('2026-07-15 16:20:00', 4, 1, 'TRANSFERENCIA', 'PAGADA'),
 ('2026-07-28 09:30:00', 5, 2, 'TARJETA',       'PAGADA'),
 ('2026-08-03 14:00:00', 6, 3, 'CREDITO',       'PENDIENTE'),
 ('2026-08-19 10:45:00', 1, 1, 'EFECTIVO',      'PAGADA'),
 ('2026-08-27 17:10:00', 7, 2, 'TARJETA',       'PAGADA'),
 ('2026-09-04 12:00:00', 8, 3, 'TRANSFERENCIA', 'PAGADA'),
 ('2026-09-16 15:30:00', 2, 1, 'TRANSFERENCIA', 'PAGADA'),
 ('2026-09-29 11:20:00', 9, 2, 'EFECTIVO',      'PAGADA'),
 ('2026-10-03 10:00:00', 4, 3, 'EFECTIVO',      'PAGADA'),
 ('2026-10-08 16:45:00', 3, 1, 'TARJETA',       'PAGADA'),
 ('2026-10-14 09:15:00', 6, 2, 'TRANSFERENCIA', 'PAGADA'),
 ('2026-10-17 18:00:00', 5, 3, 'TARJETA',       'PAGADA');

-- ---------------------------------------------------------------------
-- Detalle de ventas (id_venta, id_producto, cantidad, precio, descuento)
-- ---------------------------------------------------------------------
INSERT INTO detalle_venta (id_venta, id_producto, cantidad, precio_unitario, descuento) VALUES
 (1,  1,  1, 2799000, 0),
 (1,  5,  1,   45000, 0),
 (2,  2,  3, 3199000, 0.05),
 (2,  7,  3,  649000, 0),
 (2,  6,  3,   32000, 0),
 (2,  5,  3,   45000, 0),
 (3, 11,  1,  189000, 0),
 (3, 10,  2,  139000, 0),
 (4, 19,  4,  189000, 0),
 (4, 20,  4,  119000, 0),
 (4,  8,  4,  159000, 0),
 (4, 14,  1,  199000, 0),
 (5, 13,  1, 1649000, 0),
 (5, 12,  1,  299000, 0),
 (6,  4,  2, 1899000, 0),
 (6, 15,  2,  119000, 0),
 (6, 16,  1,  489000, 0),
 (7,  9,  1,  329000, 0),
 (8, 18,  1, 1199000, 0),
 (8, 17,  1,  299000, 0),
 (9,  7,  4,  649000, 0.05),
 (9,  6,  4,   32000, 0),
 (9,  5,  4,   45000, 0),
 (9,  9,  1,  329000, 0),
 (10, 11, 10,  189000, 0.10),
 (10, 10, 10,  139000, 0.10),
 (11,  3,  1, 5499000, 0),
 (12, 17,  2,  299000, 0),
 (12, 20,  2,  119000, 0),
 (13,  8,  1,  159000, 0),
 (13, 19,  1,  189000, 0),
 (14,  1,  2, 2799000, 0),
 (14, 14,  2,  199000, 0),
 (14, 15,  1,  119000, 0),
 (15,  9,  2,  329000, 0),
 (15, 13,  1, 1649000, 0),
 (15, 12,  1,  299000, 0);

-- La venta 12 se anula: el trigger trg_venta_anular devuelve el stock
UPDATE venta SET estado = 'ANULADA' WHERE id_venta = 12;
