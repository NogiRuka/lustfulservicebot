#!/bin/bash

# 桜色服务助手 - 数据备份脚本
# 用于备份数据库和重要配置文件

set -e  # 遇到错误时退出

# 配置变量
BACKUP_DIR="/opt/lustfulservicebot/backups"
APP_DIR="/opt/lustfulservicebot"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查是否为root用户或有sudo权限
check_permissions() {
    if [[ $EUID -eq 0 ]]; then
        log_info "以root用户运行备份脚本"
    elif sudo -n true 2>/dev/null; then
        log_info "检测到sudo权限"
    else
        log_error "需要root权限或sudo权限来运行此脚本"
        exit 1
    fi
}

# 创建备份目录
create_backup_dir() {
    if [[ ! -d "$BACKUP_DIR" ]]; then
        mkdir -p "$BACKUP_DIR"
        log_info "创建备份目录: $BACKUP_DIR"
    fi
}

# 备份数据库
backup_database() {
    local db_file="$APP_DIR/db/bot.db"
    local backup_file="$BACKUP_DIR/bot_$DATE.db"
    
    if [[ -f "$db_file" ]]; then
        cp "$db_file" "$backup_file"
        log_info "数据库备份完成: $backup_file"
        
        # 压缩备份文件
        gzip "$backup_file"
        log_info "数据库备份已压缩: $backup_file.gz"
    else
        log_warn "数据库文件不存在: $db_file"
    fi
}

# 备份配置文件
backup_config() {
    local env_file="$APP_DIR/.env"
    local backup_file="$BACKUP_DIR/env_$DATE.backup"
    
    if [[ -f "$env_file" ]]; then
        cp "$env_file" "$backup_file"
        log_info "配置文件备份完成: $backup_file"
    else
        log_warn "配置文件不存在: $env_file"
    fi
}

# 备份日志文件（最近7天）
backup_logs() {
    local logs_dir="$APP_DIR/logs"
    local backup_logs_dir="$BACKUP_DIR/logs_$DATE"
    
    if [[ -d "$logs_dir" ]]; then
        mkdir -p "$backup_logs_dir"
        
        # 备份最近7天的日志
        find "$logs_dir" -name "*.log" -mtime -7 -exec cp {} "$backup_logs_dir/" \;
        
        # 压缩日志备份
        tar -czf "$backup_logs_dir.tar.gz" -C "$BACKUP_DIR" "logs_$DATE"
        rm -rf "$backup_logs_dir"
        
        log_info "日志文件备份完成: $backup_logs_dir.tar.gz"
    else
        log_warn "日志目录不存在: $logs_dir"
    fi
}

# 清理旧备份
cleanup_old_backups() {
    log_info "清理 $RETENTION_DAYS 天前的备份文件..."
    
    # 清理数据库备份
    find "$BACKUP_DIR" -name "bot_*.db.gz" -mtime +$RETENTION_DAYS -delete 2>/dev/null || true
    
    # 清理配置备份
    find "$BACKUP_DIR" -name "env_*.backup" -mtime +$RETENTION_DAYS -delete 2>/dev/null || true
    
    # 清理日志备份
    find "$BACKUP_DIR" -name "logs_*.tar.gz" -mtime +$RETENTION_DAYS -delete 2>/dev/null || true
    
    log_info "旧备份清理完成"
}

# 显示备份统计
show_backup_stats() {
    log_info "备份统计信息:"
    echo "  备份目录: $BACKUP_DIR"
    echo "  备份时间: $DATE"
    
    if [[ -d "$BACKUP_DIR" ]]; then
        local db_count=$(find "$BACKUP_DIR" -name "bot_*.db.gz" | wc -l)
        local config_count=$(find "$BACKUP_DIR" -name "env_*.backup" | wc -l)
        local logs_count=$(find "$BACKUP_DIR" -name "logs_*.tar.gz" | wc -l)
        local total_size=$(du -sh "$BACKUP_DIR" | cut -f1)
        
        echo "  数据库备份: $db_count 个文件"
        echo "  配置备份: $config_count 个文件"
        echo "  日志备份: $logs_count 个文件"
        echo "  总大小: $total_size"
    fi
}

# 主函数
main() {
    log_info "开始备份桜色服务助手数据..."
    
    check_permissions
    create_backup_dir
    
    backup_database
    backup_config
    backup_logs
    
    cleanup_old_backups
    show_backup_stats
    
    log_info "备份完成！"
}

# 脚本帮助信息
show_help() {
    echo "桜色服务助手 - 数据备份脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help     显示此帮助信息"
    echo "  -d, --dir DIR  指定备份目录 (默认: $BACKUP_DIR)"
    echo "  -r, --retention DAYS  设置备份保留天数 (默认: $RETENTION_DAYS)"
    echo ""
    echo "示例:"
    echo "  $0                    # 使用默认设置进行备份"
    echo "  $0 -d /backup         # 指定备份目录"
    echo "  $0 -r 60             # 保留60天的备份"
}

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -d|--dir)
            BACKUP_DIR="$2"
            shift 2
            ;;
        -r|--retention)
            RETENTION_DAYS="$2"
            shift 2
            ;;
        *)
            log_error "未知参数: $1"
            show_help
            exit 1
            ;;
    esac
done

# 运行主函数
main