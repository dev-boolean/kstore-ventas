-- =====================================================================
--  KStore S.A.S. - Ejemplos de operaciones DML para la sustentación
--  Se pueden copiar y pegar en la opción "Consola SQL" de la aplicación.
-- =====================================================================

-- ---------- INSERCIÓN ----------
INSERT INTO proveedor (nit, nombre, direccion)
VALUES ('900111222-1', 'Proveedor de Prueba S.A.S.', 'Calle 1 # 2-3, Barranquilla');

INSERT INTO cliente (tipo_doc, identificacion, nombre, apellidos, direccion, fecha_nacimiento)
VALUES ('CC', '1234567890', 'Cliente', 'De Prueba', 'Carrera 10 # 20-30, Soledad', '2002-06-15');

INSERT INTO producto (codigo, nombre, precio_unitario, id_proveedor)
VALUES ('PER-005', 'Parlantes Genius SP-HF180', 59000, 1);

-- ---------- ACTUALIZACIÓN ----------
UPDATE producto SET precio_unitario = ROUND(precio_unitario * 1.05, 0)
 WHERE id_proveedor = 4;

UPDATE cliente SET direccion = 'Calle 99 # 50-10, Barranquilla'
 WHERE identificacion = '1234567890';

-- ---------- ELIMINACIÓN ----------
DELETE FROM cliente WHERE identificacion = '1234567890';

-- ---------- PRUEBAS DE INTEGRIDAD (deben FALLAR) ----------
-- 1. UNIQUE: identificación repetida
INSERT INTO cliente (tipo_doc, identificacion, nombre, apellidos, direccion, fecha_nacimiento)
VALUES ('CC', '1045678912', 'Duplicado', 'Prueba', 'Calle 1', '2000-01-01');

-- 2. FOREIGN KEY: proveedor inexistente
INSERT INTO producto (codigo, nombre, precio_unitario, id_proveedor)
VALUES ('X-001', 'Producto huérfano', 1000, 99);

-- 3. ON DELETE RESTRICT: el cliente 1 tiene pedidos
DELETE FROM cliente WHERE id_cliente = 1;

-- 4. ON DELETE RESTRICT: el proveedor 1 suministra productos
DELETE FROM proveedor WHERE id_proveedor = 1;

-- 5. CHECK: precio negativo
UPDATE producto SET precio_unitario = -100 WHERE id_producto = 1;

-- 6. CHECK: NIT con dígito de verificación equivocado (el correcto es 1)
INSERT INTO proveedor (nit, nombre, direccion)
VALUES ('900111222-5', 'Proveedor DV malo', 'Calle 1');

-- 7. CHECK: fecha de nacimiento inválida (30 de febrero)
INSERT INTO cliente (tipo_doc, identificacion, nombre, apellidos, direccion, fecha_nacimiento)
VALUES ('CC', '1112223334', 'Fecha', 'Mala', 'Calle 1', '2001-02-30');
