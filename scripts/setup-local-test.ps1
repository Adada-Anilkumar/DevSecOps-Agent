# DevSecOps Agent - Local Testing Setup (PowerShell)
Write-Host "🚀 DevSecOps Agent - Local Testing Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if .env exists
if (-not (Test-Path .env)) {
    Write-Host "📝 Creating .env file..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    Write-Host "✅ .env created" -ForegroundColor Green
    Write-Host ""
    Write-Host "⚠️  IMPORTANT: Edit .env and add your API keys:" -ForegroundColor Yellow
    Write-Host "   - OPENAI_API_KEY=sk-..."
    Write-Host "   - GITHUB_TOKEN=ghp_..."
    Write-Host "   - GITHUB_WEBHOOK_SECRET=your-secret"
    Write-Host ""
    Read-Host "Press Enter after you've edited .env"
} else {
    Write-Host "✅ .env file exists" -ForegroundColor Green
}

# Load .env
Get-Content .env | ForEach-Object {
    if ($_ -match '^([^=]+)=(.*)$') {
        $name = $matches[1]
        $value = $matches[2]
        [Environment]::SetEnvironmentVariable($name, $value, "Process")
    }
}

# Check if API keys are set
if (-not $env:OPENAI_API_KEY -or $env:OPENAI_API_KEY -eq "sk-...") {
    Write-Host "❌ OPENAI_API_KEY not set in .env" -ForegroundColor Red
    exit 1
}

if (-not $env:GITHUB_TOKEN) {
    Write-Host "⚠️  GITHUB_TOKEN not set - webhook won't be able to post comments" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow
pip install -q -r requirements.txt
pip install -q -e .
Write-Host "✅ Dependencies installed" -ForegroundColor Green

Write-Host ""
Write-Host "🔧 Testing configuration..." -ForegroundColor Yellow
python -c "from devsecops_agent.settings import get_settings; get_settings()" 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Configuration valid" -ForegroundColor Green
} else {
    Write-Host "❌ Configuration error - check your .env file" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "🏥 Starting health check..." -ForegroundColor Yellow
$job = Start-Job -ScriptBlock { python -m devsecops_agent.webhook.serve }
Start-Sleep -Seconds 3

try {
    $response = Invoke-WebRequest -Uri http://localhost:8080/health -UseBasicParsing
    if ($response.Content -match "ok") {
        Write-Host "✅ Server is healthy" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Server health check failed" -ForegroundColor Red
    Stop-Job $job
    Remove-Job $job
    exit 1
}

Stop-Job $job
Remove-Job $job

Write-Host ""
Write-Host "✅ Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Next steps:" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Start the agent:"
Write-Host "   python -m devsecops_agent.webhook.serve"
Write-Host ""
Write-Host "2. In another terminal, expose with ngrok:"
Write-Host "   ngrok http 8080"
Write-Host ""
Write-Host "3. Configure GitHub webhook:"
Write-Host "   - URL: https://YOUR-NGROK-URL.ngrok.io/webhook"
Write-Host "   - Secret: (value from GITHUB_WEBHOOK_SECRET in .env)"
Write-Host "   - Events: Pull requests"
Write-Host ""
Write-Host "4. Create a test PR and watch it work!"
Write-Host ""
Write-Host "📖 Full guide: docs/LOCAL_TESTING.md" -ForegroundColor Cyan
