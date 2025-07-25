-- 🔍 PRUEBAS DE CONTEO DE RETARDOS
-- =====================================

-- TEST 1: Conteo básico de retardos HOY
-- Debería mostrar el número de retardos del día actual
SELECT COUNT(*) as retardos_hoy 
FROM core_registro 
WHERE estado_id = 1 
  AND TIME(tiempo) > '08:10:00' 
  AND TIME(tiempo) < '12:00:00'
  AND DATE(tiempo) = CURDATE();

-- TEST 2: Conteo de retardos ESTA SEMANA (días laborales)
-- Debería mostrar retardos de los últimos 7 días, solo lunes-viernes
SELECT COUNT(*) as retardos_semana
FROM core_registro 
WHERE estado_id = 1 
  AND TIME(tiempo) > '08:10:00' 
  AND TIME(tiempo) < '12:00:00'
  AND DATE(tiempo) >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
  AND WEEKDAY(tiempo) < 5;

-- TEST 3: Conteo de retardos POR PERSONA (Top 5)
-- Debería mostrar quiénes tienen más retardos en el último mes
SELECT nombre, COUNT(*) as total_retardos
FROM core_registro 
WHERE estado_id = 1 
  AND TIME(tiempo) > '08:10:00' 
  AND TIME(tiempo) < '12:00:00'
  AND DATE(tiempo) >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
  AND WEEKDAY(tiempo) < 5
GROUP BY nombre, usuario_id
ORDER BY total_retardos DESC 
LIMIT 5;

-- TEST 4: Conteo de retardos EN JULIO 2025
-- Debería mostrar total retardos y personas afectadas en julio
SELECT COUNT(*) as retardos_julio,
       COUNT(DISTINCT usuario_id) as personas_con_retardos
FROM core_registro 
WHERE estado_id = 1 
  AND TIME(tiempo) > '08:10:00' 
  AND TIME(tiempo) < '12:00:00'
  AND DATE(tiempo) BETWEEN '2025-07-01' AND '2025-07-31'
  AND WEEKDAY(tiempo) < 5;

-- TEST 5: Retardos con MINUTOS DE RETRASO detallados
-- Debería mostrar retardos recientes con cuántos minutos llegaron tarde
SELECT nombre, 
       DATE(tiempo) as fecha,
       TIME(tiempo) as hora_llegada,
       TIMESTAMPDIFF(MINUTE, TIME('08:10:00'), TIME(tiempo)) as minutos_retardo
FROM core_registro 
WHERE estado_id = 1 
  AND TIME(tiempo) > '08:10:00' 
  AND TIME(tiempo) < '12:00:00'
  AND tiempo >= DATE_SUB(NOW(), INTERVAL 7 DAY)
ORDER BY tiempo DESC 
LIMIT 10;

-- TEST 6: Comparación días con más retardos
-- Debería mostrar qué días de la semana hay más retardos
SELECT DAYNAME(tiempo) as dia_semana,
       COUNT(*) as total_retardos
FROM core_registro 
WHERE estado_id = 1 
  AND TIME(tiempo) > '08:10:00' 
  AND TIME(tiempo) < '12:00:00'
  AND DATE(tiempo) >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
  AND WEEKDAY(tiempo) < 5
GROUP BY DAYNAME(tiempo), WEEKDAY(tiempo)
ORDER BY total_retardos DESC;

-- TEST 7: Promedio de minutos de retardo por persona
-- Debería calcular el promedio de minutos de retardo de cada persona
SELECT nombre,
       COUNT(*) as veces_tarde,
       AVG(TIMESTAMPDIFF(MINUTE, TIME('08:10:00'), TIME(tiempo))) as promedio_minutos_retardo
FROM core_registro 
WHERE estado_id = 1 
  AND TIME(tiempo) > '08:10:00' 
  AND TIME(tiempo) < '12:00:00'
  AND DATE(tiempo) >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
  AND WEEKDAY(tiempo) < 5
GROUP BY nombre, usuario_id
HAVING veces_tarde > 0
ORDER BY promedio_minutos_retardo DESC
LIMIT 5; 