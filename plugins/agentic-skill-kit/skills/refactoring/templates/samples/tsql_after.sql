-- Sample (fake schema): recalculate flight load AFTER refactoring (T-SQL, same results).
-- Steps: guard clause + RETURN, cursor -> set-based SUM, CTE for readability,
-- duplicated subquery -> join to the row being updated.
-- Preserved on purpose: NULL StatusCode rows are excluded (the cursor's @st <> 'CXL'
-- was UNKNOWN for NULL); empty flight gives 0 not NULL; totals stay DECIMAL(12,2).
-- Assumes FlightId is the primary key of dbo.Flight (the old scalar subquery needed that too).
-- Side effect removed: the old default-GLOBAL cursor named "c" could collide between sessions.
CREATE OR ALTER PROCEDURE dbo.usp_RecalcFlightLoad
    @FlightId INT
AS
BEGIN
    SET NOCOUNT ON;

    IF NOT EXISTS (SELECT 1 FROM dbo.Flight WHERE FlightId = @FlightId)
    BEGIN
        RAISERROR('Flight not found', 16, 1);
        RETURN;
    END;

    WITH Totals AS (
        SELECT CAST(COALESCE(SUM(b.WeightKg), 0) AS DECIMAL(12,2)) AS TotalKg,
               COALESCE(SUM(b.Pieces), 0)                          AS TotalPcs
        FROM dbo.Booking AS b
        WHERE b.FlightId = @FlightId
          AND b.StatusCode <> 'CXL'
    )
    UPDATE f
    SET f.TotalKg    = t.TotalKg,
        f.TotalPcs   = t.TotalPcs,
        f.LoadStatus = CASE
                           WHEN t.TotalKg > f.MaxPayloadKg       THEN 'OVR'
                           WHEN t.TotalKg > f.MaxPayloadKg * 0.9 THEN 'NRF'
                           ELSE 'OK'
                       END
    FROM dbo.Flight AS f
    CROSS JOIN Totals AS t
    WHERE f.FlightId = @FlightId;
END;
GO
