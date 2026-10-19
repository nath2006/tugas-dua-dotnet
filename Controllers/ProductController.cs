using IF133.Tugas1.Api.Data;
using IF133.Tugas1.Api.Entities;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;

namespace IF133.Tugas1.Api.Controllers;

[ApiController]
[Route("api/[controller]")]
public class ProductsController : ControllerBase
{
    private readonly AppDbContext _context;

    public ProductsController(AppDbContext context)
    {
        _context = context;
    }

    // GET /api/products
    [HttpGet]
    public async Task<ActionResult<IEnumerable<Product>>> GetAll()
    {
        var products = await _context.Products.ToListAsync();
        return Ok(products); // 200
    }

    // GET /api/products/{id}
    [HttpGet("{id}")]
    public async Task<ActionResult<Product>> GetById(int id)
    {
        var product = await _context.Products.FindAsync(id);
        if (product == null)
            return NotFound(); // 404

        return Ok(product); // 200
    }

    // POST /api/products
    [HttpPost]
    public async Task<ActionResult<Product>> Create(Product product)
    {
        product.Id = 0; // Id dibuat otomatis oleh database
        _context.Products.Add(product);
        await _context.SaveChangesAsync();

        return CreatedAtAction(nameof(GetById), new { id = product.Id }, product); // 201
    }

    // PUT /api/products/{id}
    [HttpPut("{id}")]
    public async Task<IActionResult> Update(int id, Product input)
    {
        if (id != input.Id)
            return BadRequest("Id di URL dan di body harus sama"); // 400

        var product = await _context.Products.FindAsync(id);
        if (product == null)
            return NotFound(); // 404

        product.Name = input.Name;
        product.Description = input.Description;
        product.Price = input.Price;
        product.Stock = input.Stock;

        await _context.SaveChangesAsync();
        return NoContent(); // 204
    }

    // DELETE /api/products/{id}
    [HttpDelete("{id}")]
    public async Task<IActionResult> Delete(int id)
    {
        var product = await _context.Products.FindAsync(id);
        if (product == null)
            return NotFound(); // 404

        _context.Products.Remove(product);
        await _context.SaveChangesAsync();
        return NoContent(); // 204
    }
}