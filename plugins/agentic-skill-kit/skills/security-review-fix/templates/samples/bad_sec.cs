// Deliberately VULNERABLE sample for sec_scan.py - fake secrets, do not copy.
using System.Runtime.Serialization.Formatters.Binary;
using System.Security.Cryptography;

public class AwbController : ControllerBase
{
    private const string ConnStr = "Server=db01;Database=Cargo;User Id=sa;Password=Sup3rS3cret!;";   // conn-string-password
    private static readonly string AwsKey = "__FAKE_AWS_KEY_1__";                                   // aws-access-key
    private const string ApiSecret = "q8Xf2LmZ9vR4tK7pW1sD6hJ3nB5cY0aE";                              // high-entropy-secret

    [HttpGet("{awb}")]
    public IActionResult Get(string awb)
    {
        var sql = "SELECT * FROM Awb WHERE Number = '" + awb + "'";                                   // sql-injection
        var cmd2 = $"DELETE FROM Awb WHERE Number = '{awb}'";                                          // sql-injection
        _logger.LogInformation("Login for {User} with password {Password}", user, password);         // sensitive-logging
        return Ok();
    }

    public object Load(Stream s) => new BinaryFormatter().Deserialize(s);                           // insecure-deserialize

    public string HashPassword(string password) => Convert.ToHexString(MD5.HashData(Encoding.UTF8.GetBytes(password))); // weak-password-hash

    public string NewResetToken() => new Random().Next().ToString();  // reset token                  insecure-random

    public HttpClient Client() => new(new HttpClientHandler {
        ServerCertificateCustomValidationCallback = (m, c, ch, e) => true });                        // tls-verify-off
}

// Program.cs
// builder.Services.AddCors(o => o.AddPolicy("all", p => p.SetIsOriginAllowed(_ => true).AllowCredentials()));
public static class CorsSetup
{
    public static void Add(IServiceCollection s) =>
        s.AddCors(o => o.AddPolicy("all", p => p.SetIsOriginAllowed(origin => true).AllowAnyHeader().AllowCredentials())); // cors-any-credentials
}
