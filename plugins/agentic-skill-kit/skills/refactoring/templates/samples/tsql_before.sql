-- Sample (fake schema): recalculate flight load BEFORE refactoring (T-SQL).
-- Smells: cursor for a simple aggregate, arrow-shaped IF nesting, duplicated
-- subquery, magic status codes, no early exit.
CREATE PROCEDURE dbo.usp_RecalcFlightLoad
    @FlightId INT
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @kg DECIMAL(12,2), @pcs INT, @totKg DECIMAL(12,2), @totPcs INT, @st CHAR(3);
    SET @totKg = 0;
    SET @totPcs = 0;
    IF EXISTS (SELECT 1 FROM dbo.Flight WHERE FlightId = @FlightId)
    BEGIN
        DECLARE c CURSOR FOR
            SELECT b.WeightKg, b.Pieces, b.StatusCode
            FROM dbo.Booking b
            WHERE b.FlightId = @FlightId;
        OPEN c;
        FETCH NEXT FROM c INTO @kg, @pcs, @st;
        WHILE @@FETCH_STATUS = 0
        BEGIN
            IF @st <> 'CXL'
            BEGIN
                IF @kg IS NOT NULL
                BEGIN
                    SET @totKg = @totKg + @kg;
                END
                SET @totPcs = @totPcs + ISNULL(@pcs, 0);
            END
            FETCH NEXT FROM c INTO @kg, @pcs, @st;
        END
        CLOSE c;
        DEALLOCATE c;
        UPDATE dbo.Flight
        SET TotalKg = @totKg,
            TotalPcs = @totPcs,
            LoadStatus = CASE
                WHEN @totKg > (SELECT MaxPayloadKg FROM dbo.Flight WHERE FlightId = @FlightId) THEN 'OVR'
                WHEN @totKg > (SELECT MaxPayloadKg FROM dbo.Flight WHERE FlightId = @FlightId) * 0.9 THEN 'NRF'
                ELSE 'OK'
            END
        WHERE FlightId = @FlightId;
    END
    ELSE
    BEGIN
        RAISERROR('Flight not found', 16, 1);
    END
END
GO
