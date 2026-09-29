// Clean sample for sec_scan.py: expected 0 findings.
using System.Security.Cryptography;
using Microsoft.AspNetCore.Identity;

public class AwbController(IConfiguration config, ILogger<AwbController> logger, CargoDb db) : ControllerBase
{
    private readonly string _connStr = config.GetConnectionString("Cargo")!;   // from Key Vault / env

    [HttpGet("{awb}")]
    public async Task<IActionResult> Get(string awb, CancellationToken ct)
    {
        await using var cmd = new SqlCommand("SELECT Id, Status FROM Awb WHERE Number = @awb", _conn);
        cmd.Parameters.Add("@awb", SqlDbType.VarChar, 12).Value = awb;
        logger.LogInformation("AWB lookup {AwbNumber} by {UserId}", awb, User.FindFirst("sub")?.Value);
        return Ok(await db.Awbs.Where(a => a.Number == awb).Select(a => new { a.Number, a.Status }).FirstOrDefaultAsync(ct));
    }

    public string NewResetToken() => Convert.ToHexString(RandomNumberGenerator.GetBytes(32));

    public string Hash(PasswordHasher<User> hasher, User u, string secretInput) => hasher.HashPassword(u, secretInput);
}

public static class CorsSetup
{
    public static void Add(IServiceCollection s) =>
        s.AddCors(o => o.AddPolicy("spa", p => p.WithOrigins("https://portal.example.com").AllowCredentials()));
}
