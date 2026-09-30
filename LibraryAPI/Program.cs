using System.Text;
using LibraryAPI.Data;
using LibraryAPI.Repositories;
using LibraryAPI.Services;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.EntityFrameworkCore;
using Microsoft.IdentityModel.Tokens;
using Microsoft.OpenApi.Models;

var builder = WebApplication.CreateBuilder(args);

// 1. Add Controllers & API Explorer
builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();

// 2. Configure Swagger with JWT Bearer Support
builder.Services.AddSwaggerGen(c =>
{
    c.SwaggerDoc("v1", new OpenApiInfo
    {
        Title = "LibraryAPI - Week 4 Secured",
        Version = "v1",
        Description = "ASP.NET Core Web API with JWT Authentication & Role-Based Authorization (Admin / User)."
    });

    // Define JWT Bearer security scheme
    c.AddSecurityDefinition("Bearer", new OpenApiSecurityScheme
    {
        Description = "JWT Authorization header using the Bearer scheme. Example: \"Authorization: Bearer {token}\"",
        Name = "Authorization",
        In = ParameterLocation.Header,
        Type = SecuritySchemeType.Http,
        Scheme = "Bearer",
        BearerFormat = "JWT"
    });

    c.AddSecurityRequirement(new OpenApiSecurityRequirement
    {
        {
            new OpenApiSecurityScheme
            {
                Reference = new OpenApiReference
                {
                    Type = ReferenceType.SecurityScheme,
                    Id = "Bearer"
                }
            },
            Array.Empty<string>()
        }
    });
});

// 3. Configure Database (SQL Server with resilient InMemory fallback)
var connectionString = builder.Configuration.GetConnectionString("DefaultConnection");
builder.Services.AddDbContext<LibraryDbContext>(options =>
{
    options.UseSqlServer(connectionString);
});

bool canConnectDb = false;
try
{
    var optionsBuilder = new DbContextOptionsBuilder<LibraryDbContext>();
    optionsBuilder.UseSqlServer(connectionString);
    using var tempContext = new LibraryDbContext(optionsBuilder.Options);
    canConnectDb = tempContext.Database.CanConnect();
    if (canConnectDb)
    {
        tempContext.Database.EnsureCreated();
    }
}
catch
{
    canConnectDb = false;
}

if (canConnectDb)
{
    Console.WriteLine("[Database]: Connected to SQL Server (LibraryDb_Week3). Using EF Core BookRepository.");
    builder.Services.AddScoped<IBookRepository, BookRepository>();
}
else
{
    Console.WriteLine("[Database]: SQL Server not detected or unreachable. Using InMemoryBookRepository for live development.");
    builder.Services.AddSingleton<IBookRepository, InMemoryBookRepository>();
}

builder.Services.AddScoped<IBookService, BookService>();
builder.Services.AddTransient<ResilientPolicyDelegatingHandler>();

// Configure resilient AI Service Client with Retry & Circuit Breaker policies (Week 6)
builder.Services.AddHttpClient<IAiServiceClient, AiServiceClient>(client =>
{
    var aiBaseUrl = builder.Configuration["AiService:BaseUrl"] ?? "http://127.0.0.1:8000";
    client.BaseAddress = new Uri(aiBaseUrl);
    client.Timeout = TimeSpan.FromSeconds(15);
})
.AddHttpMessageHandler<ResilientPolicyDelegatingHandler>();

// 4. Configure JWT Authentication
var jwtKey = builder.Configuration["Jwt:Key"] ?? "SuperSecretLibraryKeyForWeek4InternshipJWTTokenValidation2026!";
var jwtIssuer = builder.Configuration["Jwt:Issuer"] ?? "LibraryAPI";
var jwtAudience = builder.Configuration["Jwt:Audience"] ?? "LibraryAppUsers";
var key = Encoding.UTF8.GetBytes(jwtKey);

builder.Services.AddAuthentication(options =>
{
    options.DefaultAuthenticateScheme = JwtBearerDefaults.AuthenticationScheme;
    options.DefaultChallengeScheme = JwtBearerDefaults.AuthenticationScheme;
})
.AddJwtBearer(options =>
{
    options.RequireHttpsMetadata = false;
    options.SaveToken = true;
    options.TokenValidationParameters = new TokenValidationParameters
    {
        ValidateIssuerSigningKey = true,
        IssuerSigningKey = new SymmetricSecurityKey(key),
        ValidateIssuer = false, // Set to true if validating specific issuer
        ValidIssuer = jwtIssuer,
        ValidateAudience = false, // Set to true if validating specific audience
        ValidAudience = jwtAudience,
        ValidateLifetime = true,
        ClockSkew = TimeSpan.Zero
    };
});

builder.Services.AddAuthorization();

// 5. Configure CORS for Angular Frontend (port 4200)
builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowAngular", policy =>
    {
        policy.WithOrigins("http://localhost:4200")
              .AllowAnyMethod()
              .AllowAnyHeader()
              .AllowCredentials();
    });
});

var app = builder.Build();

// 6. Configure HTTP Middleware Pipeline
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI(c =>
    {
        c.SwaggerEndpoint("/swagger/v1/swagger.json", "LibraryAPI v1");
    });
}

app.UseCors("AllowAngular");
app.UseHttpsRedirection();

// IMPORTANT: Authentication must come before Authorization
app.UseAuthentication();
app.UseAuthorization();

app.MapControllers();

app.Run();
