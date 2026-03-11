#!/usr/bin/env pwsh
# Start Redis Server for Nova Memory 2.0
# Central Redis that all 3 agents will connect to

Write-Host "`n" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host "STARTING CENTRAL REDIS SERVER FOR NOVA MEMORY 2.0" -ForegroundColor Green
Write-Host "============================================================`n" -ForegroundColor Green

# Check if redis-server is available
$redisCmd = Get-Command redis-server -ErrorAction SilentlyContinue

if (-not $redisCmd) {
    Write-Host "⚠ Redis server not found in PATH" -ForegroundColor Yellow
    Write-Host "`nPlease install Redis using one of these methods:" -ForegroundColor Yellow
    Write-Host "  1. Download from https://redis.io/download`n" -ForegroundColor Yellow
    Write-Host "  2. Use WSL: wsl redis-server`n" -ForegroundColor Yellow
    Write-Host "  3. Use Docker: docker run -d -p 6379:6379 redis:7-alpine`n" -ForegroundColor Yellow
    Write-Host "  4. Chocolatey: choco install redis-64`n" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "✓ Redis server found" -ForegroundColor Green
Write-Host "✓ Starting Redis on port 6379..." -ForegroundColor Green
Write-Host "  All agents will connect to: 127.0.0.1:6379" -ForegroundColor Cyan
Write-Host "  Press Ctrl+C to stop`n" -ForegroundColor Cyan

redis-server --port 6379

Read-Host "`nPress Enter to exit"
