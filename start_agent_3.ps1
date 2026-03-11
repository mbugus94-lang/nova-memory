#!/usr/bin/env pwsh
# Start Agent 3 of Nova Memory 2.0
# Connects to CENTRAL Redis and DATABASE

Write-Host "`n" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host "STARTING AGENT 3 (Port 8003)" -ForegroundColor Green
Write-Host "============================================================`n" -ForegroundColor Green

Write-Host "Configuration:" -ForegroundColor Cyan
Write-Host "  Agent ID:       agent_003" -ForegroundColor Cyan
Write-Host "  Agent Name:     Agent-3" -ForegroundColor Cyan
Write-Host "  API Port:       8003" -ForegroundColor Cyan
Write-Host "  Redis:          127.0.0.1:6379" -ForegroundColor Cyan
Write-Host "  Database:       nova_memory_central.db" -ForegroundColor Cyan
Write-Host "`nAccess at: http://localhost:8003/docs`n" -ForegroundColor Green

# Load central configuration
if (Test-Path ".env.central") {
    Write-Host "✓ Loading central configuration from .env.central" -ForegroundColor Green
} else {
    Write-Host "⚠ Warning: .env.central not found" -ForegroundColor Yellow
    Write-Host "  Creating from .env.example..." -ForegroundColor Yellow
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env.central"
    }
}

# Set agent-specific environment variables
$env:AGENT_ID = "agent_003"
$env:AGENT_NAME = "Agent-3"
$env:API_PORT = "8003"

Write-Host "`nStarting Agent 3..." -ForegroundColor Green
python api/integration.py
