-- =====================================================================
--  KStore S.A.S. - Consultas SQL (reportes)
--  La aplicación lee este archivo y muestra cada bloque en el módulo
--  "Reportes". Formato de cada bloque:
--      -- @ Título del reporte
--      -- Descripción (opcional, una o varias líneas)
--      -- grafico: columna_x, columna_y   (opcional)
--      SELECT ... ;
--  Las ventas ANULADAS no se cuentan en los reportes de ventas.
-- =====================================================================

-- @ Top 10 productos más vendidos
-- Unidades vendidas e ingresos por producto (JOIN + GROUP BY + ORDER BY + LIMIT).
-- grafico: producto, unidades
SELECT p.codigo,
       p.nombre                                               AS producto,
       SUM(d.cantidad)                                        AS unidades,
       ROUND(SUM(d.cantidad * d.precio_unitario * (1 - d.descuento)), 0) AS ingresos
  FROM detalle_venta d
  JOIN producto p ON p.id_producto = d.id_producto
  JOIN venta    v ON v.id_venta    = d.id_venta
 WHERE v.estado <> 'ANULADA'
 GROUP BY p.id_producto
 ORDER BY unidades DESC, ingresos DESC
 LIMIT 10;

-- @ Ventas por mes
-- Número de facturas y total facturado (con IVA) agrupado por mes.
-- grafico: mes, total
SELECT strftime('%Y-%m', fecha) AS mes,
       COUNT(*)                 AS facturas,
       SUM(subtotal)            AS subtotal,
       SUM(total)               AS total
  FROM v_venta_resumen
 WHERE estado <> 'ANULADA'
 GROUP BY mes
 ORDER BY mes;

-- @ Ranking de clientes por compras
-- Cuánto ha comprado cada cliente y cuándo fue su última compra.
SELECT c.documento,
       c.nombre,
       c.tipo,
       COUNT(r.id_venta) AS compras,
       SUM(r.total)      AS total_comprado,
       MAX(r.fecha)      AS ultima_compra
  FROM cliente c
  JOIN v_venta_resumen r ON r.id_cliente = c.id_cliente
 WHERE r.estado <> 'ANULADA'
 GROUP BY c.id_cliente
 ORDER BY total_comprado DESC;

-- @ Clientes que nunca han comprado
-- LEFT JOIN + IS NULL: clientes registrados sin ninguna venta asociada.
SELECT c.id_cliente, c.documento, c.nombre, c.ciudad, c.fecha_registro
  FROM cliente c
  LEFT JOIN venta v ON v.id_cliente = c.id_cliente
 WHERE v.id_venta IS NULL;

-- @ Clientes que compran por encima del promedio
-- Subconsulta en HAVING: clientes cuyo total supera el promedio por cliente.
SELECT c.nombre,
       SUM(r.total) AS total_comprado
  FROM cliente c
  JOIN v_venta_resumen r ON r.id_cliente = c.id_cliente
 WHERE r.estado <> 'ANULADA'
 GROUP BY c.id_cliente
HAVING SUM(r.total) > (SELECT AVG(t) FROM (SELECT SUM(total) AS t
                                              FROM v_venta_resumen
                                             WHERE estado <> 'ANULADA'
                                             GROUP BY id_cliente))
 ORDER BY total_comprado DESC;

-- @ Ventas por categoría
-- Ingresos y unidades agrupados por categoría de producto.
-- grafico: categoria, ingresos
SELECT cat.nombre                                             AS categoria,
       SUM(d.cantidad)                                        AS unidades,
       ROUND(SUM(d.cantidad * d.precio_unitario * (1 - d.descuento)), 0) AS ingresos
  FROM categoria cat
  JOIN producto p      ON p.id_categoria = cat.id_categoria
  JOIN detalle_venta d ON d.id_producto  = p.id_producto
  JOIN venta v         ON v.id_venta     = d.id_venta
 WHERE v.estado <> 'ANULADA'
 GROUP BY cat.id_categoria
 ORDER BY ingresos DESC;

-- @ Desempeño y comisión por vendedor
-- Ventas realizadas, total vendido (sin IVA) y comisión ganada.
-- grafico: vendedor, vendido
SELECT ve.nombre                              AS vendedor,
       COUNT(r.id_venta)                      AS ventas,
       COALESCE(SUM(r.subtotal), 0)           AS vendido,
       ve.comision * 100                      AS comision_pct,
       ROUND(COALESCE(SUM(r.subtotal), 0) * ve.comision, 0) AS comision_ganada
  FROM vendedor ve
  LEFT JOIN v_venta_resumen r ON r.id_vendedor = ve.id_vendedor
                             AND r.estado <> 'ANULADA'
 GROUP BY ve.id_vendedor
 ORDER BY vendido DESC;

-- @ Productos con stock bajo
-- Productos cuyo inventario está en o por debajo del mínimo.
SELECT p.codigo, p.nombre, cat.nombre AS categoria, p.stock, p.stock_minimo,
       p.stock_minimo - p.stock + 5 AS sugerido_pedir
  FROM producto p
  JOIN categoria cat ON cat.id_categoria = p.id_categoria
 WHERE p.stock <= p.stock_minimo
 ORDER BY p.stock;

-- @ Productos que nunca se han vendido
-- Subconsulta con NOT EXISTS.
SELECT p.codigo, p.nombre, p.precio, p.stock
  FROM producto p
 WHERE NOT EXISTS (SELECT 1 FROM detalle_venta d
                    WHERE d.id_producto = p.id_producto);

-- @ Ventas pendientes de pago (crédito)
-- Facturas en estado PENDIENTE con los datos de contacto del cliente.
SELECT r.id_venta, r.fecha, r.cliente, c.telefono, c.email, r.total,
       CAST(julianday('now', 'localtime') - julianday(r.fecha) AS INTEGER) AS dias
  FROM v_venta_resumen r
  JOIN cliente c ON c.id_cliente = r.id_cliente
 WHERE r.estado = 'PENDIENTE'
 ORDER BY r.fecha;

-- @ Ventas por método de pago
-- grafico: metodo_pago, total
SELECT metodo_pago, COUNT(*) AS facturas, SUM(total) AS total
  FROM v_venta_resumen
 WHERE estado <> 'ANULADA'
 GROUP BY metodo_pago
 ORDER BY total DESC;

-- @ Ventas por ciudad
-- grafico: ciudad, total
SELECT c.ciudad, COUNT(r.id_venta) AS facturas, SUM(r.total) AS total
  FROM v_venta_resumen r
  JOIN cliente c ON c.id_cliente = r.id_cliente
 WHERE r.estado <> 'ANULADA'
 GROUP BY c.ciudad
 ORDER BY total DESC;

-- @ Detalle completo de facturas
-- JOIN de cinco tablas: venta, cliente, vendedor, detalle_venta y producto.
SELECT v.id_venta, v.fecha, c.nombre AS cliente, ve.nombre AS vendedor,
       p.nombre AS producto, d.cantidad, d.precio_unitario, d.descuento,
       ROUND(d.cantidad * d.precio_unitario * (1 - d.descuento), 0) AS valor,
       v.estado
  FROM venta v
  JOIN cliente c        ON c.id_cliente   = v.id_cliente
  JOIN vendedor ve      ON ve.id_vendedor = v.id_vendedor
  JOIN detalle_venta d  ON d.id_venta     = v.id_venta
  JOIN producto p       ON p.id_producto  = d.id_producto
 ORDER BY v.id_venta, p.nombre;
