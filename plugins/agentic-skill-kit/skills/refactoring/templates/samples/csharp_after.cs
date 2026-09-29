// Sample (fake data): shipment status text AFTER refactoring (same behaviour).
// Steps: guard clauses, lookup table for status codes, replace magic number,
// simplify boolean checks, loop -> List.ConvertAll, remove dead code.
// Kept on purpose: public signatures (incl. the `upper` flag), current-culture
// formatting of weight and ToUpper(), "Unknown status" for a null status,
// NullReferenceException when `items` is null (ConvertAll, not LINQ Select).
using System;
using System.Collections.Generic;

namespace Demo.Samples
{
    public record Shipment(string Awb, string Status, int Pieces, double Weight, bool IsTransit, string Station);

    public class ShipmentHelper
    {
        private const int AwbLength = 12;

        private static readonly Dictionary<string, string> StatusText = new()
        {
            ["RCS"] = "Received at",
            ["DEP"] = "Departed from",
            ["ARR"] = "Arrived at",
            ["DLV"] = "Delivered at",
        };

        public string Describe(string awb, string status, int pieces, double weight, bool isTransit, string station, bool upper)
        {
            ArgumentNullException.ThrowIfNull(awb);
            if (awb.Length != AwbLength)
                throw new ArgumentException("AWB must be 12 characters");

            // null check first: Dictionary lookups throw on a null key, the old == did not
            var text = status is not null && StatusText.TryGetValue(status, out var prefix)
                ? $"{prefix} {station}"
                : "Unknown status";
            if (isTransit && (status is "ARR" or "DEP"))
                text += " (transit)";
            text += $" - {pieces} pcs / {weight:0.0} kg";
            return upper ? text.ToUpper() : text;
        }

        public List<string> DescribeAll(List<Shipment> items) =>
            items.ConvertAll(s => Describe(s.Awb, s.Status, s.Pieces, s.Weight, s.IsTransit, s.Station, false));
    }
}
