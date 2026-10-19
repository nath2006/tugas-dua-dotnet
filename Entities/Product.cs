using System.ComponentModel.DataAnnotations;

namespace IF133.Tugas1.Api.Entities;

public class Product
{
    public int Id { get; set; }

    [Required(ErrorMessage = "Name wajib diisi")]
    [StringLength(100)]
    public string Name { get; set; } = string.Empty;

    [StringLength(500)]
    public string? Description { get; set; }

    [Range(0, 999999999, ErrorMessage = "Price harus >= 0")]
    public decimal Price { get; set; }

    [Range(0, int.MaxValue, ErrorMessage = "Stock harus >= 0")]
    public int Stock { get; set; }
}