-- =====================================================================
--  KStore S.A.S. - Ejemplos de operaciones DML para la sustentación
--  Se pueden copiar y pegar en el módulo "Consola SQL" de la aplicación.
-- =====================================================================

-- ---------- INSERCIÓN ----------
INSERT INTO cliente (tipo_doc, documento, nombre, tipo, email, telefono, ciudad)
VALUES ('CC', '1234567890', 'Cliente de Prueba', 'PERSONA', 'prueba@correo.com', '3000000000', 'Barranquilla');

INSERT INTO producto (codigo, nombre, id_categoria, precio, stock, stock_minimo)
VALUES ('PER-006', 'Parlantes Genius SP-HF180', 2, 59000, 20, 5);

-- ---------- ACTUALIZACIÓN ----------
-- Subir 5 % el precio de todos los productos de la categoría Gaming
UPDATE producto
   SET precio = ROUND(precio * 1.05, 0)
 WHERE id_categoria = (SELECT id_categoria FROM categoria WHERE nombre = 'Gaming');

-- Registrar el pago de una venta a crédito
UPDATE venta SET estado = 'PAGADA' WHERE id_venta = 6;

-- Anular una venta (el trigger devuelve el stock)
UPDATE venta SET estado = 'ANULADA' WHERE id_venta = 15;

-- ---------- ELIMINACIÓN ----------
DELETE FROM cliente WHERE documento = '1234567890';

-- ---------- PRUEBAS DE INTEGRIDAD (deben FALLAR) ----------
-- 1. Clave primaria / UNIQUE duplicada
INSERT INTO cliente (tipo_doc, documento, nombre, tipo, ciudad)
VALUES ('CC', '1045678912', 'Duplicado', 'PERSONA', 'Barranquilla');

-- 2. Clave foránea inexistente (no hay categoría 99)
INSERT INTO producto (codigo, nombre, id_categoria, precio, stock)
VALUES ('X-001', 'Producto huérfano', 99, 1000, 1);

-- 3. ON DELETE RESTRICT: el cliente 1 tiene ventas
DELETE FROM cliente WHERE id_cliente = 1;

-- 4. CHECK: precio negativo
UPDATE producto SET precio = -100 WHERE id_producto = 1;

-- 5. CHECK: una empresa debe tener NIT
INSERT INTO cliente (tipo_doc, documento, nombre, tipo, ciudad)
VALUES ('CC', '5555555', 'Empresa mal registrada', 'EMPRESA', 'Soledad');

-- 5b. CHECK: cédula con formato inválido (letras)
INSERT INTO cliente (tipo_doc, documento, nombre, tipo, ciudad)
VALUES ('CC', '10A5678', 'Cédula inválida', 'PERSONA', 'Soledad');

-- 5c. CHECK: NIT con dígito de verificación equivocado (el correcto de 900111222 es 1)
INSERT INTO cliente (tipo_doc, documento, nombre, tipo, ciudad)
VALUES ('NIT', '900111222-5', 'Empresa DV malo', 'EMPRESA', 'Soledad');

-- 6. Trigger: vender más de lo que hay en stock
INSERT INTO venta (id_cliente, id_vendedor, metodo_pago) VALUES (1, 1, 'EFECTIVO');
INSERT INTO detalle_venta (id_venta, id_producto, cantidad, precio_unitario)
VALUES (last_insert_rowid(), 3, 999, 5499000);
