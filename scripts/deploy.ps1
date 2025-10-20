# PowerShell 部署脚本 - 用于 Windows 环境手动部署和管理数据库

param(
    [switch]$ResetDb,
    [switch]$KeepDb,
    [switch]$Help
)

# 显示帮助信息
function Show-Help {
    Write-Host "用法: .\scripts\deploy.ps1 [选项]" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "选项:" -ForegroundColor Cyan
    Write-Host "  -ResetDb      重置数据库（删除所有数据并重建）"
    Write-Host "  -KeepDb       保留数据库数据（默认）"
    Write-Host "  -Help         显示此帮助信息"
    Write-Host ""
    Write-Host "示例:" -ForegroundColor Cyan
    Write-Host "  .\scripts\deploy.ps1                # 正常部署，保留数据库"
    Write-Host "  .\scripts\deploy.ps1 -ResetDb       # 部署并重置数据库"
}

if ($Help) {
    Show-Help
    exit 0
}

Write-Host "========================================" -ForegroundColor Green
Write-Host "   Ditan Backend 部署脚本" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# 停止容器
Write-Host "🛑 停止旧容器..." -ForegroundColor Yellow
if ($ResetDb) {
    Write-Host "🗑️  删除数据库volume..." -ForegroundColor Yellow
    docker-compose down -v
} else {
    Write-Host "💾 保留数据库数据..." -ForegroundColor Yellow
    docker-compose down
}

# 拉取最新镜像
Write-Host "⬇️  拉取最新镜像..." -ForegroundColor Yellow
docker-compose pull

# 启动容器
Write-Host "🚀 启动新容器..." -ForegroundColor Yellow
docker-compose up -d

# 等待服务启动
Write-Host "⏳ 等待服务启动..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# 检查容器状态
Write-Host "📊 检查容器状态..." -ForegroundColor Yellow
docker-compose ps

# 健康检查
Write-Host "🏥 检查应用健康状态..." -ForegroundColor Yellow
$APP_PORT = if ($env:APP_PORT) { $env:APP_PORT } else { "8000" }
$healthCheckPassed = $false

for ($i = 1; $i -le 5; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:${APP_PORT}/health" -UseBasicParsing -TimeoutSec 5
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ 应用健康检查通过" -ForegroundColor Green
            Write-Host ""
            Write-Host "========================================" -ForegroundColor Green
            Write-Host "🎉 部署成功！" -ForegroundColor Green
            Write-Host "🔗 应用地址: http://localhost:${APP_PORT}" -ForegroundColor Green
            Write-Host "========================================" -ForegroundColor Green
            $healthCheckPassed = $true
            break
        }
    } catch {
        Write-Host "⏳ 等待应用就绪... ($i/5)" -ForegroundColor Yellow
        Start-Sleep -Seconds 5
    }
}

if (-not $healthCheckPassed) {
    Write-Host "⚠️  健康检查未通过，请查看日志:" -ForegroundColor Red
    docker-compose logs --tail=50 app
    exit 1
}

