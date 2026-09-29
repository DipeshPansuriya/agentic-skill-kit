-- Deliberately bad sample for scripts/sql_lint.py (fake data)
SELECT * FROM shipment s, awb_event e
WHERE s.awb_no = e.awb_no;

SELECT awb_no, status_code
FROM awb_event
WHERE YEAR(event_ts) = 2026
  AND LOWER(station) = 'dxb'
ORDER BY event_ts DESC;

SELECT c.customer_id
FROM customer c
WHERE c.customer_id NOT IN (SELECT consignee_id FROM shipment);

SELECT awb_no FROM shipment WHERE awb_no LIKE '%5675';

UPDATE shipment SET status = 'DLV';

DELETE FROM uld_scan;

DECLARE @sql nvarchar(max) = N'SELECT awb_no FROM shipment WHERE station = ''' + @station + N'''';
EXEC(@sql);

-- A good query: should produce no findings
SELECT s.awb_no, s.status
FROM shipment AS s
JOIN awb_event AS e ON e.awb_no = s.awb_no
WHERE s.created_at >= '2026-09-01' AND s.created_at < '2026-10-01'
ORDER BY s.created_at
LIMIT 100;
