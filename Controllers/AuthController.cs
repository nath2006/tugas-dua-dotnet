using IF133.Tugas1.Api.DTOs.Auth;
using System.IdentityModel.Tokens.Jwt;
using System.Security.Claims;
using System.Security.Cryptography;
using System.Text;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.IdentityModel.Tokens;

namespace IF133.Tugas1.Api.Controllers;


[ApiController]
[Route("api/auth")]
public sealed class AuthController(IConfiguration configuration, ILogger<AuthController> logger) : ControllerBase
{
    [AllowAnonymous]
    [HttpPost("login")]
    [ProducesResponseType(typeof(LoginResponseDto), StatusCodes.Status200OK)]
    [ProducesResponseType(typeof(ValidationProblemDetails), StatusCodes.Status400BadRequest)]
    [ProducesResponseType(typeof(ProblemDetails), StatusCodes.Status401Unauthorized)]
    public IActionResult Login(LoginRequest input)
    {
        var users = configuration.GetSection("Auth:Users").GetChildren();
        var user = users.FirstOrDefault(u => string.Equals(u["Username"], input.Username, StringComparison.Ordinal));
        var valid = VerifyPassword(input.Password, user?["PasswordHash"]);
        if (!valid || user is null)
        {
            logger.LogWarning("Login gagal. TraceId: {TraceId}", HttpContext.TraceIdentifier);
            Response.Headers.WWWAuthenticate = "Bearer";
            return Problem(statusCode: 401, title: "Autentikasi gagal", detail: "Username atau password tidak valid.");
        }
        var now = DateTime.UtcNow;
        var minutes = configuration.GetValue<int?>("Jwt:ExpiresMinutes") ?? 30;
        var token = new JwtSecurityToken(
            issuer: configuration["Jwt:Issuer"], audience: configuration["Jwt:Audience"],
            claims: new[] { new Claim(JwtRegisteredClaimNames.Sub, user["Username"]!), new Claim("role", user["Role"]!), new Claim(JwtRegisteredClaimNames.Jti, Guid.NewGuid().ToString()) },
            notBefore: now, expires: now.AddMinutes(minutes),
            signingCredentials: new SigningCredentials(new SymmetricSecurityKey(Encoding.UTF8.GetBytes(configuration["Jwt:Key"]!)), SecurityAlgorithms.HmacSha256));
        logger.LogInformation("Login berhasil. Role: {Role}, TraceId: {TraceId}", user["Role"], HttpContext.TraceIdentifier);
        return Ok(new LoginResponseDto(new JwtSecurityTokenHandler().WriteToken(token), "Bearer", minutes * 60));
    }

    private static bool VerifyPassword(string password, string? encoded)
    {
        // Perform the same expensive derivation for unknown users to limit timing disclosure.
        var iterations = 210000;
        var salt = new byte[16];
        var expected = new byte[32];
        var validFormat = false;
        if (encoded is not null)
        {
            try
            {
                var parts = encoded.Split('.');
                if (parts.Length == 3 && int.TryParse(parts[0], out var parsed) && parsed is >= 100000 and <= 1000000)
                {
                    var parsedSalt = Convert.FromBase64String(parts[1]);
                    var parsedHash = Convert.FromBase64String(parts[2]);
                    if (parsedSalt.Length >= 16 && parsedHash.Length == 32)
                    {
                        iterations = parsed; salt = parsedSalt; expected = parsedHash; validFormat = true;
                    }
                }
            }
            catch (FormatException) { /* Invalid configured hashes never authenticate. */ }
        }
        var actual = Rfc2898DeriveBytes.Pbkdf2(password, salt, iterations, HashAlgorithmName.SHA256, 32);
        return CryptographicOperations.FixedTimeEquals(actual, expected) && validFormat;
    }
}
