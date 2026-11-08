using Microsoft.IdentityModel.Tokens;
using System.Text;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using IF133.Tugas1.Api.Data;
using Microsoft.AspNetCore.Diagnostics;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;

var builder = WebApplication.CreateBuilder(args);
IF133.Tugas1.Api.Configuration.AuthConfiguration.Validate(builder.Configuration);
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(options =>
{
    options.AddSecurityDefinition("Bearer", new Microsoft.OpenApi.OpenApiSecurityScheme
    {
        Type = Microsoft.OpenApi.SecuritySchemeType.Http,
        Scheme = "bearer",
        BearerFormat = "JWT",
        Description = "Login melalui /api/auth/login, lalu masukkan accessToken (tanpa awalan Bearer)."
    });
    options.AddSecurityRequirement(document => new Microsoft.OpenApi.OpenApiSecurityRequirement
    {
        [new Microsoft.OpenApi.OpenApiSecuritySchemeReference("Bearer", document)] = new List<string>()
    });
    options.OperationFilter<IF133.Tugas1.Api.OpenApi.AnonymousOperationFilter>();
});
// ======================================================
// 1. DATABASE
// ======================================================

var connectionString = builder.Configuration
    .GetConnectionString("DefaultConnection");

if (string.IsNullOrWhiteSpace(connectionString))
{
    throw new InvalidOperationException(
        "Connection string DefaultConnection belum dikonfigurasi."
    );
}

builder.Services.AddDbContext<AppDbContext>(options =>
{
    options.UseMySql(
        connectionString,
        ServerVersion.AutoDetect(connectionString)
    );
});

// ======================================================
// 2. CONTROLLER DAN VALIDASI REQUEST
// ======================================================

builder.Services.AddControllers()
    .ConfigureApiBehaviorOptions(options =>
    {
        options.InvalidModelStateResponseFactory = context =>
        {
            var traceId = context.HttpContext.TraceIdentifier;

            var logger = context.HttpContext.RequestServices
                .GetRequiredService<ILoggerFactory>()
                .CreateLogger("RequestValidation");

            logger.LogWarning(
                "Validasi request gagal. Method: {Method}, " +
                "Path: {Path}, TraceId: {TraceId}",
                context.HttpContext.Request.Method,
                context.HttpContext.Request.Path,
                traceId
            );

            var problem = new ValidationProblemDetails(
                context.ModelState)
            {
                Status = StatusCodes.Status400BadRequest,
                Title = "Validasi gagal",
                Detail = "Periksa kembali data yang dikirim.",
                Instance = context.HttpContext.Request.Path.Value
            };

            problem.Extensions["traceId"] = traceId;

            var result = new BadRequestObjectResult(problem);
            result.ContentTypes.Add("application/problem+json");

            return result;
        };
    });

// ======================================================
// 3. PROBLEM DETAILS
// ======================================================

builder.Services.AddProblemDetails(options =>
{
    options.CustomizeProblemDetails = context =>
    {
        context.ProblemDetails.Instance ??=
            context.HttpContext.Request.Path.Value;

        context.ProblemDetails.Extensions["traceId"] =
            context.HttpContext.TraceIdentifier;
    };
});


// ======================================================
// 5. CORS
// Membaca Cors:AllowedOrigins dari konfigurasi.
// Default development: frontend lokal port 5173.
// Environment lain tanpa konfigurasi tidak mengizinkan origin.
// ======================================================

const string corsPolicyName = "FrontendPolicy";

var configuredOrigins = builder.Configuration
    .GetSection("Cors:AllowedOrigins")
    .Get<string[]>();

var allowedOrigins = configuredOrigins
    ?? (builder.Environment.IsDevelopment()
        ? new[] { "http://localhost:5173" }
        : Array.Empty<string>());

builder.Services.AddCors(options =>
{
    options.AddPolicy(corsPolicyName, policy =>
    {
        if (allowedOrigins.Length > 0)
        {
            policy.WithOrigins(allowedOrigins)
                .WithMethods("GET", "POST", "PUT", "DELETE")
                .WithHeaders("Content-Type", "Authorization");
        }
    });
});

builder.Services.AddAuthentication("Bearer").AddJwtBearer(options =>
{
    options.MapInboundClaims = false;
    options.IncludeErrorDetails = false;
    options.TokenValidationParameters = new TokenValidationParameters
    {
        ValidateIssuer = true, ValidateAudience = true,
        ValidateIssuerSigningKey = true, ValidateLifetime = true,
        RequireExpirationTime = true, RequireSignedTokens = true,
        ValidIssuer = builder.Configuration["Jwt:Issuer"],
        ValidAudience = builder.Configuration["Jwt:Audience"],
        IssuerSigningKey = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(builder.Configuration["Jwt:Key"]!)),
        ValidAlgorithms = new[] { SecurityAlgorithms.HmacSha256 },
        ClockSkew = TimeSpan.FromSeconds(30),
        NameClaimType = "sub", RoleClaimType = "role"
    };
});
builder.Services.AddAuthorization();

var app = builder.Build();
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI(options =>
    {
        options.SwaggerEndpoint("/swagger/v1/swagger.json", "IF133 Product API v1");
        options.RoutePrefix = "swagger";
    });
}
// ======================================================
// 6. GLOBAL EXCEPTION HANDLER
// Detail exception hanya dicatat pada log server.
// ======================================================

app.UseExceptionHandler(errorApp =>
{
    errorApp.Run(async context =>
    {
        var exceptionFeature = context.Features
            .Get<IExceptionHandlerFeature>();

        var logger = context.RequestServices
            .GetRequiredService<ILoggerFactory>()
            .CreateLogger("GlobalExceptionHandler");

        logger.LogError(
            exceptionFeature?.Error,
            "Unexpected error. Method: {Method}, " +
            "Path: {Path}, TraceId: {TraceId}",
            context.Request.Method,
            context.Request.Path,
            context.TraceIdentifier
        );

        await Results.Problem(
            statusCode: StatusCodes.Status500InternalServerError,
            title: "Terjadi kesalahan pada server",
            detail: "Silakan coba kembali atau hubungi administrator.",
            instance: context.Request.Path.Value,
            extensions: new Dictionary<string, object?>
            {
                ["traceId"] = context.TraceIdentifier
            }
        ).ExecuteAsync(context);
    });
});

// ======================================================
// 7. ERROR STATUS TANPA BODY
// Contoh: URL tidak ditemukan atau method tidak didukung.
// ======================================================

app.UseStatusCodePages(async statusContext =>
{
    var context = statusContext.HttpContext;
    var statusCode = context.Response.StatusCode;

    var title = statusCode switch
    {
        StatusCodes.Status400BadRequest =>
            "Request tidak valid",

        StatusCodes.Status401Unauthorized =>
            "Autentikasi diperlukan",

        StatusCodes.Status403Forbidden =>
            "Akses ditolak",

        StatusCodes.Status404NotFound =>
            "Resource tidak ditemukan",

        StatusCodes.Status405MethodNotAllowed =>
            "HTTP method tidak diizinkan",

        StatusCodes.Status415UnsupportedMediaType =>
            "Format konten tidak didukung",

        _ => "Request tidak dapat diproses"
    };

    await Results.Problem(
        statusCode: statusCode,
        title: title,
        instance: context.Request.Path.Value,
        extensions: new Dictionary<string, object?>
        {
            ["traceId"] = context.TraceIdentifier
        }
    ).ExecuteAsync(context);
});


// ======================================================
// 9. HTTP PIPELINE
// ======================================================

app.UseHttpsRedirection();

app.UseRouting();

app.UseCors(corsPolicyName);

app.UseAuthentication();
app.UseAuthorization();

app.MapControllers();

app.Run();