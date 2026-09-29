-- Sample (fake schema): dwell-time report AFTER refactoring (PostgreSQL, same result set).
-- Steps: loop -> RETURN QUERY, nested IF -> WHERE + COALESCE, IF ladder -> CASE,
-- CTE names the computed value once. Signature unchanged.
-- Columns are qualified (s., d.) because the OUT names awb_no etc. are variables too.
CREATE OR REPLACE FUNCTION cargo.dwell_report(p_station text, p_as_of timestamptz)
RETURNS TABLE (awb_no text, dwell_hours numeric, dwell_band text)
LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    WITH dwell AS (
        SELECT s.awb_no::text AS awb,
               round(extract(epoch FROM (coalesce(s.delivered_at, p_as_of) - s.received_at)) / 3600, 1) AS hours
        FROM cargo.shipment AS s
        WHERE s.station = p_station
          AND s.received_at IS NOT NULL
    )
    SELECT d.awb, d.hours,
           CASE WHEN d.hours < 24 THEN 'GREEN'
                WHEN d.hours < 72 THEN 'AMBER'
                ELSE 'RED' END
    FROM dwell AS d;
END;
$$;
