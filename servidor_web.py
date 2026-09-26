-- Agregar las columnas nuevas (sin la columna "codigo")
ALTER TABLE clientes ADD COLUMN apellidos VARCHAR(100);
ALTER TABLE clientes ADD COLUMN calle VARCHAR(100);
ALTER TABLE clientes ADD COLUMN mz VARCHAR(10);
ALTER TABLE clientes ADD COLUMN lote VARCHAR(10);
ALTER TABLE clientes ADD COLUMN fecha_pago DATE;
ALTER TABLE clientes ADD COLUMN fecha_corte DATE;
ALTER TABLE clientes ADD COLUMN monto_pagar NUMERIC(10,2);
ALTER TABLE clientes ADD COLUMN mes VARCHAR(20);
ALTER TABLE clientes ADD COLUMN estado VARCHAR(20) DEFAULT 'Puntual';

-- Insertar el cliente de ejemplo (Y. Cleiver)
INSERT INTO clientes (nombre_completo, apellidos, dni, calle, mz, lote, fecha_pago, fecha_corte, monto_pagar, mes, estado, usuario)
VALUES ('Y. Cleiver', 'P. Calua', '76742965', 'Uruguay', 'U', '6', '2026-08-01', '2026-12-05', 10.00, 'enero', 'Puntual', 'SM7665');

-- Ver el resultado
SELECT * FROM clientes;
