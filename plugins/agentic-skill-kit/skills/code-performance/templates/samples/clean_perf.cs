// Clean sample for perf_smells.py: expected 0 HIGH / 0 MED.
using System.Text;
using System.Text.RegularExpressions;

public partial class AwbService
{
    private static readonly Regex AwbFormat = new(@"^\d{3}-\d{8}$", RegexOptions.Compiled);

    public async Task<string> BuildManifestAsync(IReadOnlyList<Awb> awbs, IReadOnlySet<string> blockedSet, CancellationToken ct)
    {
        var shipperIds = awbs.Select(a => a.ShipperId).Distinct().ToList();
        var shippers = await _context.Shippers.AsNoTracking()
            .Where(s => shipperIds.Contains(s.Id))
            .ToDictionaryAsync(s => s.Id, s => s.Name, ct);

        var sb = new StringBuilder();
        foreach (var awb in awbs)
        {
            if (blockedSet.Contains(awb.Id)) continue;
            sb.Append(awb.Number).Append(',').Append(shippers[awb.ShipperId]).Append('\n');
        }
        await _context.SaveChangesAsync(ct);
        return sb.ToString();
    }
}
