using System.ComponentModel.DataAnnotations;

namespace IF133.Tugas1.Api.DTOs.Products;

public class CreateProductDto
{
    [Required(ErrorMessage = "Nama produk wajib diisi")]
    [StringLength(100)]
    public string Name {
        get;
        set;
    } = string.Empty;

    [StringLength(500)]
    public string? Description {
        get;
        set;
    }

    [Required(ErrorMessage = "Harga wajib diisi")]
    [Range(typeof(decimal), "0", "999999999",
        ErrorMessage = "Harga harus antara 0 dan 999999999")]
    public decimal? Price {
        get;
        set;
    }

    [Required(ErrorMessage = "Stok wajib diisi")]
    [Range(0, int.MaxValue, ErrorMessage = "Stok tidak boleh negatif")]
    public int? Stock {
        get;
        set;
    }
}
