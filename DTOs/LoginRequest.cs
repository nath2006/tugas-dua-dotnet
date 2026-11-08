using System.ComponentModel.DataAnnotations;

namespace IF133.Tugas1.Api.DTOs.Auth;

public sealed class LoginRequest
{
    [Required, StringLength(100)]
    public string Username { get; set; } = string.Empty;

    [Required, StringLength(1024)]
    public string Password { get; set; } = string.Empty;
}

public sealed record LoginResponseDto(string AccessToken, string TokenType, int ExpiresIn);
