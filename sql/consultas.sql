-- =====================================================================
--  KStore S.A.S. - Consultas SQL pedidas en el laboratorio
--  La aplicación lee este archivo y muestra cada bloque en la opción
--  "Consultas". Formato de cada bloque:
--      -- @ Título de la consulta
--      -- Descripción (opcional)
--      SELECT ... ;
-- =====================================================================

-- @ Consulta 1 · Clientes y cantidad de pedidos realizados
-- LEFT JOIN + GROUP BY: también aparecen los clientes con 0 pedidos.
SELECT c.tipo_doc,
       c.identificacion,
       c.nombre,
       c.apellidos,
       COUNT(pe.id_pedido) AS cantidad_pedidos
  FROM cliente c
  LEFT JOIN pedido pe ON pe.id_cliente = c.id_cliente
 GROUP BY c.id_cliente
 ORDER BY cantidad_pedidos DESC, c.apellidos;

-- @ Consulta 2 · Clientes que no realizaron ningún pedido
-- LEFT JOIN + IS NULL: clientes sin ninguna fila en PEDIDO.
SELECT c.tipo_doc,
       c.identificacion,
       c.nombre,
       c.apellidos,
       c.direccion
  FROM cliente c
  LEFT JOIN pedido pe ON pe.id_cliente = c.id_cliente
 WHERE pe.id_pedido IS NULL
 ORDER BY c.apellidos;

-- @ Consulta 3 · Cliente, producto, cantidad, precio de compra y proveedor
-- JOIN de cinco tablas: cliente, pedido, detalle_pedido, producto y proveedor.
SELECT c.nombre || ' ' || c.apellidos  AS cliente,
       pr.nombre                       AS producto,
       d.cantidad                      AS cantidad_comprada,
       d.precio_compra                 AS precio_compra,
       pv.nombre                       AS proveedor
  FROM cliente c
  JOIN pedido pe         ON pe.id_cliente   = c.id_cliente
  JOIN detalle_pedido d  ON d.id_pedido     = pe.id_pedido
  JOIN producto pr       ON pr.id_producto  = d.id_producto
  JOIN proveedor pv      ON pv.id_proveedor = pr.id_proveedor
 ORDER BY cliente, pe.fecha, producto;

-- @ Consulta 4 · Proveedores con los productos suministrados
-- LEFT JOIN: también aparecen los proveedores que aún no suministran productos.
SELECT pv.nit,
       pv.nombre                               AS proveedor,
       COALESCE(pr.codigo, '-')                AS codigo,
       COALESCE(pr.nombre, '(sin productos)')  AS producto,
       pr.precio_unitario
  FROM proveedor pv
  LEFT JOIN producto pr ON pr.id_proveedor = pv.id_proveedor
 ORDER BY pv.nombre, pr.codigo;
