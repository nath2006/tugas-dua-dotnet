using IF133.Tugas1.Api.Data;
using IF133.Tugas1.Api.DTOs.Products;
using IF133.Tugas1.Api.Entities;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Authorization;
using Microsoft.EntityFrameworkCore;

namespace IF133.Tugas1.Api.Controllers;

[Authorize(Roles = "Admin,Reader")]
[ApiController]
[Route("api/products")]
[ProducesResponseType(typeof(ProblemDetails), StatusCodes.Status401Unauthorized)]
[ProducesResponseType(typeof(ProblemDetails), StatusCodes.Status403Forbidden)]
[ProducesResponseType(typeof(ProblemDetails), StatusCodes.Status500InternalServerError)]
public class ProductsController : ControllerBase
{
    private readonly AppDbContext _context;
    private readonly ILogger<ProductsController> _logger;

    public ProductsController(
        AppDbContext context,
        ILogger<ProductsController> logger)
    {
        _context = context;
        _logger = logger;
    }

    // GET: /api/products
    [HttpGet]
    [ProducesResponseType(typeof(IEnumerable<ProductResponseDto>), StatusCodes.Status200OK)]
    public async Task<ActionResult<IEnumerable<ProductResponseDto>>> GetAll()
    {
        var products = await _context.Products
            .AsNoTracking()
            .ToListAsync();

        _logger.LogInformation(
            "Daftar produk diambil. Jumlah: {Count}, TraceId: {TraceId}",
            products.Count,
            HttpContext.TraceIdentifier
        );

        return Ok(products.Select(ToDto));
    }

    // GET: /api/products/1
    [HttpGet("{id:int}")]
    [ProducesResponseType(typeof(ProductResponseDto), StatusCodes.Status200OK)]
    [ProducesResponseType(typeof(ProblemDetails), StatusCodes.Status404NotFound)]
    public async Task<ActionResult<ProductResponseDto>> GetById(int id)
    {
        var product = await _context.Products
            .AsNoTracking()
            .FirstOrDefaultAsync(p => p.Id == id);

        if (product == null)
        {
            return ProductNotFound(id);
        }

        _logger.LogInformation(
            "Detail produk diambil. ProductId: {ProductId}, TraceId: {TraceId}",
            id,
            HttpContext.TraceIdentifier
        );

        return Ok(ToDto(product));
    }

    // POST: /api/products
    [HttpPost]
    [Authorize(Roles = "Admin")]
    [ProducesResponseType(typeof(ProductResponseDto), StatusCodes.Status201Created)]
    [ProducesResponseType(typeof(ValidationProblemDetails), StatusCodes.Status400BadRequest)]
    [ProducesResponseType(typeof(ProblemDetails), StatusCodes.Status415UnsupportedMediaType)]
    public async Task<ActionResult<ProductResponseDto>> Create(
        CreateProductDto input)
    {
        var product = new Product
        {
            Name = input.Name.Trim(),
            Description = input.Description,
            Price = input.Price!.Value,
            Stock = input.Stock!.Value
        };

        _context.Products.Add(product);
        await _context.SaveChangesAsync();

        _logger.LogInformation(
            "Produk dibuat. ProductId: {ProductId}, TraceId: {TraceId}",
            product.Id,
            HttpContext.TraceIdentifier
        );

        return CreatedAtAction(
            nameof(GetById),
            new { id = product.Id },
            ToDto(product)
        );
    }

    // PUT: /api/products/1
    [HttpPut("{id:int}")]
    [Authorize(Roles = "Admin")]
    [ProducesResponseType(StatusCodes.Status204NoContent)]
    [ProducesResponseType(typeof(ValidationProblemDetails), StatusCodes.Status400BadRequest)]
    [ProducesResponseType(typeof(ProblemDetails), StatusCodes.Status404NotFound)]
    [ProducesResponseType(typeof(ProblemDetails), StatusCodes.Status415UnsupportedMediaType)]
    public async Task<IActionResult> Update(
        int id,
        UpdateProductDto input)
    {
        var product = await _context.Products.FindAsync(id);

        if (product == null)
        {
            return ProductNotFound(id);
        }

        product.Name = input.Name.Trim();
        product.Description = input.Description;
        product.Price = input.Price!.Value;
        product.Stock = input.Stock!.Value;

        await _context.SaveChangesAsync();

        _logger.LogInformation(
            "Produk diperbarui. ProductId: {ProductId}, TraceId: {TraceId}",
            id,
            HttpContext.TraceIdentifier
        );

        return NoContent();
    }

    // DELETE: /api/products/1
    [HttpDelete("{id:int}")]
    [Authorize(Roles = "Admin")]
    [ProducesResponseType(StatusCodes.Status204NoContent)]
    [ProducesResponseType(typeof(ProblemDetails), StatusCodes.Status404NotFound)]
    public async Task<IActionResult> Delete(int id)
    {
        var product = await _context.Products.FindAsync(id);

        if (product == null)
        {
            return ProductNotFound(id);
        }

        _context.Products.Remove(product);
        await _context.SaveChangesAsync();

        _logger.LogInformation(
            "Produk dihapus. ProductId: {ProductId}, TraceId: {TraceId}",
            id,
            HttpContext.TraceIdentifier
        );

        return NoContent();
    }

    // Respons dan logging untuk produk yang tidak ditemukan.
    private ObjectResult ProductNotFound(int id)
    {
        _logger.LogWarning(
            "Produk tidak ditemukan. ProductId: {ProductId}, " +
            "Method: {Method}, TraceId: {TraceId}",
            id,
            HttpContext.Request.Method,
            HttpContext.TraceIdentifier
        );

        return Problem(
            statusCode: StatusCodes.Status404NotFound,
            title: "Produk tidak ditemukan",
            detail: $"Produk dengan ID {id} tidak tersedia.",
            instance: HttpContext.Request.Path.Value
        );
    }

    // Mapping Entity menjadi response DTO.
    private static ProductResponseDto ToDto(Product product)
    {
        return new ProductResponseDto
        {
            Id = product.Id,
            Name = product.Name,
            Description = product.Description,
            Price = product.Price,
            Stock = product.Stock
        };
    }
}