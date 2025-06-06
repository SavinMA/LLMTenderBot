#!/usr/bin/env pwsh

# LLMTenderBot Deployment Script for Windows
# Usage: .\deploy.ps1 [dev|prod]

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("dev", "prod")]
    [string]$Environment = "dev"
)

$ErrorActionPreference = "Stop"

$ComposeFile = "docker-compose.yml"
if ($Environment -eq "prod") {
    $ComposeFile = "docker-compose.prod.yml"
}

Write-Host "🚀 Deploying LLMTenderBot in $Environment mode..."

# Check if .env file exists
if (!(Test-Path ".env")) {
    Write-Host "❌ .env file not found. Please copy example.env to .env and configure it."
    exit 1
}

# Check if Docker is running
try {
    docker info | Out-Null
} catch {
    Write-Host "❌ Docker is not running. Please start Docker first."
    exit 1
}

# Create necessary directories
Write-Host "📁 Creating directories..."
New-Item -ItemType Directory -Force -Path "logs", "data" | Out-Null

# Stop existing containers
Write-Host "🛑 Stopping existing containers..."
docker-compose -f $ComposeFile down

# Build and start services
Write-Host "🔨 Building and starting services..."
docker-compose -f $ComposeFile up --build -d

# Wait for services to be healthy
Write-Host "⏳ Waiting for services to start..."
Start-Sleep -Seconds 10

# Check status
Write-Host "📊 Checking service status..."
docker-compose -f $ComposeFile ps

# Test Ollama connection
Write-Host "🧪 Testing Ollama connection..."
$timeout = 30
$timer = 0
$ollamaReady = $false

while ($timer -lt $timeout) {
    try {
        Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -Method GET -TimeoutSec 2 | Out-Null
        $ollamaReady = $true
        break
    } catch {
        Start-Sleep -Seconds 2
        $timer += 2
    }
}

if ($ollamaReady) {
    Write-Host "✅ Ollama is ready"
} else {
    Write-Host "⚠️ Ollama might not be ready yet"
}

# Show logs
Write-Host "📝 Recent logs:"
docker-compose -f $ComposeFile logs --tail=20

Write-Host ""
Write-Host "✅ Deployment completed!"
Write-Host ""
Write-Host "📋 Useful commands:"
Write-Host "  View logs: docker-compose -f $ComposeFile logs -f"
Write-Host "  Stop: docker-compose -f $ComposeFile down"
Write-Host "  Restart: docker-compose -f $ComposeFile restart"
Write-Host "  Pull Ollama model: docker exec -it ollama ollama pull llama3.2:3b"
Write-Host ""

if ($Environment -eq "prod") {
    Write-Host "Production mode active."
} 