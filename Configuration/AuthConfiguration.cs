using System.Text;

namespace IF133.Tugas1.Api.Configuration;

public static class AuthConfiguration
{
    public static void Validate(IConfiguration configuration)
    {
        var key = configuration["Jwt:Key"];
        if (string.IsNullOrWhiteSpace(key) || Encoding.UTF8.GetByteCount(key) < 32 ||
            string.IsNullOrWhiteSpace(configuration["Jwt:Issuer"]) ||
            string.IsNullOrWhiteSpace(configuration["Jwt:Audience"]) ||
            !int.TryParse(configuration["Jwt:ExpiresMinutes"] ?? "30", out var minutes) || minutes is < 1 or > 60)
        {
            throw new InvalidOperationException("Konfigurasi JWT belum valid. Atur User Secrets: key acak minimal 32 byte, issuer, audience, dan masa berlaku 1–60 menit.");
        }

        var users = configuration.GetSection("Auth:Users").GetChildren().ToArray();
        var names = new HashSet<string>(StringComparer.Ordinal);
        if (users.Length == 0 || users.Any(user =>
            string.IsNullOrWhiteSpace(user["Username"]) || user["Username"]!.Length > 100 || !names.Add(user["Username"]!) ||
            user["Role"] is not ("Admin" or "Reader") || !IsValidHash(user["PasswordHash"])))
        {
            throw new InvalidOperationException("Konfigurasi akun belum valid. Gunakan username unik, role Admin/Reader, dan hash PBKDF2-SHA256; jangan simpan password plaintext.");
        }
    }

    private static bool IsValidHash(string? encoded)
    {
        if (encoded is null) return false;
        var parts = encoded.Split('.');
        if (parts.Length != 3 || !int.TryParse(parts[0], out var iterations) || iterations is < 100000 or > 1000000)
            return false;
        try
        {
            return Convert.FromBase64String(parts[1]).Length >= 16 && Convert.FromBase64String(parts[2]).Length == 32;
        }
        catch (FormatException)
        {
            return false;
        }
    }
}
