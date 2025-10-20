# PowerShell 数据库管理脚本

param(
    [Parameter(Position=0)]
    [string]$Command
)

# 显示帮助信息
function Show-Help {
    Write-Host "数据库管理脚本" -ForegroundColor Blue
    Write-Host ""
    Write-Host "用法: .\scripts\manage_db.ps1 [命令]" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "命令:" -ForegroundColor Cyan
    Write-Host "  reset        重置数据库（删除volume并重启数据库容器）"
    Write-Host "  restart      重启数据库容器"
    Write-Host "  logs         查看数据库日志"
    Write-Host "  status       查看数据库状态"
    Write-Host "  backup       备份数据库（TODO）"
    Write-Host "  help         显示此帮助信息"
    Write-Host ""
    Write-Host "示例:" -ForegroundColor Cyan
    Write-Host "  .\scripts\manage_db.ps1 reset      # 重置数据库"
    Write-Host "  .\scripts\manage_db.ps1 logs       # 查看数据库日志"
}

# 重置数据库
function Reset-Database {
    Write-Host "⚠️  警告: 这将删除所有数据库数据！" -ForegroundColor Yellow
    $confirmation = Read-Host "确认继续？ (y/N)"
    if ($confirmation -ne 'y' -and $confirmation -ne 'Y') {
        Write-Host "操作已取消" -ForegroundColor Blue
        exit 0
    }
    
    Write-Host "🛑 停止数据库容器..." -ForegroundColor Yellow
    docker-compose stop db
    
    Write-Host "🗑️  删除数据库volume..." -ForegroundColor Yellow
    try {
        docker volume rm ditan_postgres_data
    } catch {
        Write-Host "⚠️  Volume 不存在或无法删除" -ForegroundColor Yellow
    }
    
    Write-Host "🚀 启动数据库容器..." -ForegroundColor Yellow
    docker-compose up -d db
    
    Write-Host "⏳ 等待数据库就绪..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
    
    Write-Host "🔧 初始化数据库表..." -ForegroundColor Yellow
    try {
        docker-compose exec app uv run python scripts/init_db.py
    } catch {
        Write-Host "⚠️  应用未运行或初始化脚本失败" -ForegroundColor Yellow
    }
    
    Write-Host "✅ 数据库重置完成！" -ForegroundColor Green
}

# 重启数据库
function Restart-Database {
    Write-Host "🔄 重启数据库容器..." -ForegroundColor Yellow
    docker-compose restart db
    Write-Host "✅ 数据库已重启" -ForegroundColor Green
}

# 查看日志
function Show-Logs {
    Write-Host "📋 数据库日志:" -ForegroundColor Blue
    docker-compose logs -f db
}

# 查看状态
function Show-Status {
    Write-Host "📊 数据库状态:" -ForegroundColor Blue
    docker-compose ps db
    Write-Host ""
    Write-Host "🗄️  Volume 信息:" -ForegroundColor Blue
    try {
        docker volume inspect ditan_postgres_data
    } catch {
        Write-Host "⚠️  Volume 不存在" -ForegroundColor Yellow
    }
}

# 执行命令
switch ($Command) {
    "reset" {
        Reset-Database
    }
    "restart" {
        Restart-Database
    }
    "logs" {
        Show-Logs
    }
    "status" {
        Show-Status
    }
    "backup" {
        Write-Host "⚠️  备份功能待实现" -ForegroundColor Yellow
    }
    { $_ -in "help", "--help", "-h", "" } {
        Show-Help
    }
    default {
        Write-Host "错误: 未知命令 '$Command'" -ForegroundColor Red
        Write-Host ""
        Show-Help
        exit 1
    }
}

