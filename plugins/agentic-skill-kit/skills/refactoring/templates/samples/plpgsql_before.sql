-- Sample (fake schema): dwell-time report BEFORE refactoring (PostgreSQL PL/pgSQL).
-- Smells: row-by-row FOR loop + RETURN NEXT, nested IF, duplicated epoch math, magic numbers.
CREATE OR REPLACE FUNCTION cargo.dwell_report(p_station text, p_as_of timestamptz)
RETURNS TABLE (awb_no text, dwell_hours numeric, dwell_band text)
LANGUAGE plpgsql AS $$
DECLARE
    rec     record;
    v_hours numeric;
    v_band  text;
BEGIN
    FOR rec IN SELECT s.awb_no, s.received_at, s.delivered_at
               FROM cargo.shipment s
               WHERE s.station = p_station LOOP
        IF rec.received_at IS NOT NULL THEN
            IF rec.delivered_at IS NOT NULL THEN
                v_hours := round(extract(epoch FROM (rec.delivered_at - rec.received_at)) / 3600, 1);
            ELSE
                v_hours := round(extract(epoch FROM (p_as_of - rec.received_at)) / 3600, 1);
            END IF;
            IF v_hours < 24 THEN
                v_band := 'GREEN';
            ELSIF v_hours < 72 THEN
                v_band := 'AMBER';
            ELSE
                v_band := 'RED';
            END IF;
            awb_no := rec.awb_no;
            dwell_hours := v_hours;
            dwell_band := v_band;
            RETURN NEXT;
        END IF;
    END LOOP;
END;
$$;
