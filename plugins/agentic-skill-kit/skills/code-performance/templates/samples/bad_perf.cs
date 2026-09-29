// Deliberately BAD sample for perf_smells.py - do not copy.
using System.Text.RegularExpressions;

public class AwbService
{
    private readonly CargoDbContext _context;
    private readonly HttpClient _httpClient;

    public ShipmentDto GetShipment(string awb)
    {
        var data = _httpClient.GetStringAsync($"/api/awb/{awb}").Result;          // sync-over-async
        LoadCacheAsync().Wait();                                                   // sync-over-async
        var token = GetTokenAsync().GetAwaiter().GetResult();                      // sync-over-async
        return Parse(data);
    }

    public string BuildManifest(List<Awb> awbs, List<string> blockedIds)
    {
        string csv = "";
        foreach (var awb in awbs)
        {
            var shipper = _context.Shippers.FirstOrDefault(s => s.Id == awb.ShipperId); // io-in-loop (N+1)
            if (blockedIds.Contains(awb.Id)) continue;                                 // linear-lookup-loop
            var rx = new Regex(@"^\d{3}-\d{8}$");                                      // regex-in-loop
            csv += awb.Number + "," + shipper.Name + "\n";                            // string-concat-loop
            Console.WriteLine($"Processed {awb.Number}");                             // log-in-loop
            _context.SaveChanges();                                                    // io-in-loop
        }
        return csv;
    }

    public List<Awb> Open() =>
        _context.Awbs.ToList().Where(a => a.Status == "OPEN").ToList();               // filter-in-memory

    public void Retry()
    {
        Thread.Sleep(5000);                                                            // sleep-in-code
        var sql = "SELECT * FROM Awb WHERE Status = 'OPEN'";                           // select-star
    }
}
