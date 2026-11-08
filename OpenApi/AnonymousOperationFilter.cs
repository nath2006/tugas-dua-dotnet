using Microsoft.AspNetCore.Authorization;
using Microsoft.OpenApi;
using Swashbuckle.AspNetCore.SwaggerGen;

namespace IF133.Tugas1.Api.OpenApi;

// Override the global bearer requirement for explicitly anonymous operations.
public sealed class AnonymousOperationFilter : IOperationFilter
{
    public void Apply(OpenApiOperation operation, OperationFilterContext context)
    {
        foreach (var response in operation.Responses ?? new OpenApiResponses())
        {
            if (int.TryParse(response.Key, out var status) && status >= 400)
            {
                var media = response.Value.Content?.Values.FirstOrDefault();
                if (media is not null && response.Value is OpenApiResponse concrete)
                {
                    concrete.Content = new Dictionary<string, OpenApiMediaType>
                    {
                        ["application/problem+json"] = media
                    };
                }
            }
        }
        if (context.MethodInfo.IsDefined(typeof(AllowAnonymousAttribute), true))
        {
            operation.Security = new List<OpenApiSecurityRequirement>();
        }
    }
}
