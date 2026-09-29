// Sample (fake data): shipment status text BEFORE refactoring.
// Smells: arrow-shaped nesting, if/else ladder on codes, flag argument, `== true`,
// index loop that only maps, dead private method.
using System;
using System.Collections.Generic;

namespace Demo.Samples
{
    public record Shipment(string Awb, string Status, int Pieces, double Weight, bool IsTransit, string Station);

    public class ShipmentHelper
    {
        public string Describe(string awb, string status, int pieces, double weight, bool isTransit, string station, bool upper)
        {
            string result = "";
            if (awb != null)
            {
                if (awb.Length == 12)
                {
                    if (status == "RCS")
                    {
                        result = "Received at " + station;
                    }
                    else if (status == "DEP")
                    {
                        result = "Departed from " + station;
                    }
                    else if (status == "ARR")
                    {
                        result = "Arrived at " + station;
                    }
                    else if (status == "DLV")
                    {
                        result = "Delivered at " + station;
                    }
                    else
                    {
                        result = "Unknown status";
                    }
                    if (isTransit == true)
                    {
                        if (status == "ARR" || status == "DEP")
                        {
                            result = result + " (transit)";
                        }
                    }
                    result = result + " - " + pieces + " pcs / " + weight.ToString("0.0") + " kg";
                    if (upper == true)
                    {
                        result = result.ToUpper();
                    }
                }
                else
                {
                    throw new ArgumentException("AWB must be 12 characters");
                }
            }
            else
            {
                throw new ArgumentNullException("awb");
            }
            return result;
        }

        public List<string> DescribeAll(List<Shipment> items)
        {
            List<string> list = new List<string>();
            for (int i = 0; i < items.Count; i++)
            {
                Shipment s = items[i];
                string d = Describe(s.Awb, s.Status, s.Pieces, s.Weight, s.IsTransit, s.Station, false);
                list.Add(d);
            }
            return list;
        }

        private string FormatLegacy(string awb)
        {
            // not called anywhere (checked with a solution-wide search)
            return awb.Substring(0, 3) + "-" + awb.Substring(3);
        }
    }
}
