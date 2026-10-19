-- =====================================================================
--  KStore S.A.S. - Datos de ejemplo (DML)
--  Se ejecuta después de schema.sql.
--  Todos los nombres, documentos y direcciones son ficticios.
-- =====================================================================

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------------
-- Proveedores (NIT con dígito de verificación válido).
-- El proveedor 6 todavía no suministra productos.
-- ---------------------------------------------------------------------
INSERT INTO proveedor (nit, nombre, direccion) VALUES
 ('900123456-8', 'Distribuciones Caribe Tech S.A.S.',     'Calle 77 # 59-35, Barranquilla'),
 ('901234567-7', 'Importadora Andina de Cómputo S.A.S.',  'Carrera 7 # 71-21, Bogotá'),
 ('800987654-4', 'Redes y Conectividad del Norte Ltda.',  'Vía 40 # 85-120, Barranquilla'),
 ('900555888-1', 'Gamer Supply Colombia S.A.S.',          'Calle 10 # 43D-25, Medellín'),
 ('830112233-1', 'Componentes Globales S.A.S.',           'Avenida El Dorado # 69-76, Bogotá'),
 ('901777888-6', 'Suministros de Oficina del Atlántico',  'Carrera 54 # 64-245, Barranquilla');

-- ---------------------------------------------------------------------
-- Clientes (CC o CE). Los clientes 9 y 10 no han hecho pedidos.
-- ---------------------------------------------------------------------
INSERT INTO cliente (tipo_doc, identificacion, nombre, apellidos, direccion, fecha_nacimiento) VALUES
 ('CC', '1045678912', 'Carlos Andrés',    'Pérez Gómez',       'Calle 84 # 45-20, Barranquilla',      '1998-03-14'),
 ('CC', '1129876543', 'María Fernanda',   'Gómez Ruiz',        'Carrera 38 # 30-15, Soledad',         '2001-07-22'),
 ('CC', '72145896',   'Jorge Luis',       'Martínez Orozco',   'Calle 72 # 46-80, Barranquilla',      '1979-11-02'),
 ('CC', '1043987654', 'Laura Valentina',  'Ruiz Herrera',      'Carrera 19 # 5-40, Puerto Colombia',  '2000-01-30'),
 ('CE', '845123',     'Andrea',           'Rossi',             'Calle 22 # 3-50, Santa Marta',        '1990-05-18'),
 ('CC', '32789456',   'Diana Marcela',    'Rojas Cantillo',    'Carrera 43 # 82-10, Barranquilla',    '1985-09-09'),
 ('CC', '1140333444', 'Luis Fernando',    'Castro Pertuz',     'Calle 30 # 17-55, Malambo',           '1995-12-01'),
 ('CC', '1047111222', 'Ana Lucía',        'Torres Barrios',    'Carrera 50 # 76-31, Barranquilla',    '1997-04-26'),
 ('CC', '1001234567', 'Kevin David',      'Orozco Mendoza',    'Calle 45 # 21-12, Barranquilla',      '2003-08-15'),
 ('CE', '912345',     'Sofía',            'Martín',            'Carrera 1 # 15-90, Cartagena',        '1988-02-11');

-- ---------------------------------------------------------------------
-- Productos (precio unitario en pesos colombianos)
-- ---------------------------------------------------------------------
INSERT INTO producto (codigo, nombre, precio_unitario, id_proveedor) VALUES
 ('POR-001', 'Portátil Lenovo IdeaPad 3 Ryzen 5',   2799000, 1),
 ('POR-002', 'Portátil HP 15 Core i5 16GB',         3199000, 1),
 ('POR-003', 'MacBook Air M2 13 pulgadas',          5499000, 2),
 ('PER-001', 'Mouse Logitech M170 inalámbrico',       45000, 1),
 ('PER-002', 'Teclado Genius KB-110 USB',             32000, 1),
 ('PER-003', 'Monitor Samsung 24 pulgadas Full HD',  649000, 2),
 ('PER-004', 'Diadema Logitech H390 USB',            159000, 2),
 ('COM-001', 'Memoria RAM Kingston 8GB DDR4',        139000, 5),
 ('COM-002', 'SSD Kingston A400 480GB',              189000, 5),
 ('COM-003', 'Tarjeta gráfica RTX 4060 8GB',        1649000, 5),
 ('RED-001', 'Router TP-Link Archer C6',             199000, 3),
 ('RED-002', 'Switch TP-Link 8 puertos',             119000, 3),
 ('RED-003', 'Cable UTP Cat6 caja 305 m',            489000, 3),
 ('GAM-001', 'Control Xbox inalámbrico',             299000, 4),
 ('GAM-002', 'Silla gamer Cougar Armor',            1199000, 4),
 ('GAM-003', 'Teclado mecánico Redragon Kumara',     189000, 4);

-- ---------------------------------------------------------------------
-- Pedidos (encabezado)
-- ---------------------------------------------------------------------
INSERT INTO pedido (id_cliente, fecha) VALUES
 (1, '2026-06-05 10:15:00'),
 (2, '2026-06-18 15:40:00'),
 (3, '2026-07-02 11:05:00'),
 (1, '2026-07-15 16:20:00'),
 (4, '2026-07-28 09:30:00'),
 (5, '2026-08-03 14:00:00'),
 (6, '2026-08-19 10:45:00'),
 (7, '2026-08-27 17:10:00'),
 (2, '2026-09-04 12:00:00'),
 (8, '2026-09-16 15:30:00'),
 (3, '2026-10-03 10:00:00'),
 (1, '2026-10-14 09:15:00');

-- ---------------------------------------------------------------------
-- Detalle de pedidos (id_pedido, id_producto, cantidad, precio_compra)
-- ---------------------------------------------------------------------
INSERT INTO detalle_pedido (id_pedido, id_producto, cantidad, precio_compra) VALUES
 (1,  1, 1, 2799000),
 (1,  4, 1,   45000),
 (2,  6, 2,  649000),
 (2,  5, 2,   32000),
 (3,  9, 1,  189000),
 (3,  8, 2,  139000),
 (4, 16, 1,  189000),
 (4,  7, 1,  159000),
 (5,  3, 1, 5499000),
 (6, 11, 1,  199000),
 (6, 12, 2,  119000),
 (6, 13, 1,  489000),
 (7, 10, 1, 1649000),
 (8, 15, 1, 1199000),
 (8, 14, 2,  299000),
 (9,  2, 1, 3199000),
 (9,  4, 3,   45000),
 (10, 8, 4,  139000),
 (10, 9, 2,  189000),
 (11, 14, 1, 299000),
 (12, 6, 1,  649000),
 (12, 11, 1, 199000);
