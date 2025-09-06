# 桜色服务助手 - 部署指南

## 📋 项目概述

桜色服务助手是一个功能完整的Telegram机器人，具备以下核心功能：

- **代发消息系统**：管理员可向用户发送消息并追踪回复
- **回复追踪**：自动监听用户回复并通知管理员
- **用户管理**：完整的用户角色和权限系统
- **反馈系统**：用户反馈收集和管理员回复
- **内容管理**：求片、投稿等内容管理功能
- **系统设置**：灵活的系统配置和功能开关

## 🚀 Linux服务器部署

### 1. 系统要求

- **操作系统**：Ubuntu 20.04+ / CentOS 8+ / Debian 11+
- **Python版本**：Python 3.12+
- **内存**：最低 512MB，推荐 1GB+
- **存储**：最低 1GB 可用空间
- **网络**：需要访问Telegram API

### 2. 环境准备

#### 2.1 更新系统
```bash
# Ubuntu/Debian
sudo apt update && sudo apt upgrade -y

# CentOS/RHEL
sudo yum update -y
```

#### 2.2 安装Python 3.12
```bash
# Ubuntu/Debian
sudo apt install software-properties-common -y
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install python3.12 python3.12-venv python3.12-pip -y

# CentOS/RHEL
sudo yum install python3.12 python3.12-pip -y
```

#### 2.3 安装Git
```bash
# Ubuntu/Debian
sudo apt install git -y

# CentOS/RHEL
sudo yum install git -y
```

### 3. 项目部署

#### 3.1 创建部署目录
```bash
sudo mkdir -p /opt/lustfulservicebot
sudo chown $USER:$USER /opt/lustfulservicebot
cd /opt/lustfulservicebot
```

#### 3.2 克隆项目
```bash
# 如果使用Git仓库
git clone <your-repository-url> .

# 或者上传项目文件
# 将本地项目文件上传到 /opt/lustfulservicebot/
```

#### 3.3 创建虚拟环境
```bash
python3.12 -m venv venv
source venv/bin/activate
```

#### 3.4 安装依赖
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. 配置文件设置

#### 4.1 环境变量配置
创建 `.env` 文件：
```bash
cp .env.example .env
nano .env
```

配置以下环境变量：
```env
# Telegram Bot配置
BOT_TOKEN=your_bot_token_here
SUPERADMIN_ID=your_telegram_user_id
ADMINS_ID=admin1_id,admin2_id

# 机器人设置
BOT_NICKNAME=桜色服务助手
GROUP=your_group_username  # 可选

# 数据库配置
DATABASE_URL=sqlite:///./db/bot.db

# 日志配置
LOG_LEVEL=INFO
DEBUG=False
```

#### 4.2 数据库初始化
数据库表和初始数据会在首次启动时自动创建，无需手动操作。

### 5. 系统服务配置

#### 5.1 创建systemd服务文件
```bash
sudo nano /etc/systemd/system/lustfulservicebot.service
```

服务文件内容：
```ini
[Unit]
Description=桜色服务助手 Telegram Bot
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/opt/lustfulservicebot
Environment=PATH=/opt/lustfulservicebot/venv/bin
ExecStart=/opt/lustfulservicebot/venv/bin/python -m app.bot
Restart=always
RestartSec=10

# 日志配置
StandardOutput=journal
StandardError=journal
SyslogIdentifier=lustfulservicebot

[Install]
WantedBy=multi-user.target
```

#### 5.2 启用并启动服务
```bash
# 重新加载systemd配置
sudo systemctl daemon-reload

# 启用服务（开机自启）
sudo systemctl enable lustfulservicebot

# 启动服务
sudo systemctl start lustfulservicebot

# 查看服务状态
sudo systemctl status lustfulservicebot
```

### 6. 日志管理

#### 6.1 查看实时日志
```bash
# 查看systemd日志
sudo journalctl -u lustfulservicebot -f

# 查看应用日志
tail -f /opt/lustfulservicebot/logs/all.log
```

#### 6.2 日志轮转配置
创建logrotate配置：
```bash
sudo nano /etc/logrotate.d/lustfulservicebot
```

配置内容：
```
/opt/lustfulservicebot/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 your_username your_username
    postrotate
        systemctl reload lustfulservicebot
    endscript
}
```

### 7. 安全配置

#### 7.1 防火墙设置
```bash
# Ubuntu/Debian (ufw)
sudo ufw allow ssh
sudo ufw enable

# CentOS/RHEL (firewalld)
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --reload
```

#### 7.2 文件权限
```bash
# 设置适当的文件权限
chmod 600 .env
chmod -R 755 /opt/lustfulservicebot
chmod +x run.sh
```

### 8. 备份策略

#### 8.1 数据库备份脚本
创建 `backup.sh`：
```bash
#!/bin/bash
BACKUP_DIR="/opt/lustfulservicebot/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# 备份数据库
cp /opt/lustfulservicebot/db/bot.db $BACKUP_DIR/bot_$DATE.db

# 备份配置文件
cp /opt/lustfulservicebot/.env $BACKUP_DIR/env_$DATE.backup

# 清理30天前的备份
find $BACKUP_DIR -name "*.db" -mtime +30 -delete
find $BACKUP_DIR -name "*.backup" -mtime +30 -delete

echo "备份完成: $DATE"
```

#### 8.2 设置定时备份
```bash
# 添加到crontab
crontab -e

# 每天凌晨2点备份
0 2 * * * /opt/lustfulservicebot/backup.sh
```

### 9. 监控和维护

#### 9.1 服务管理命令
```bash
# 启动服务
sudo systemctl start lustfulservicebot

# 停止服务
sudo systemctl stop lustfulservicebot

# 重启服务
sudo systemctl restart lustfulservicebot

# 查看状态
sudo systemctl status lustfulservicebot

# 查看日志
sudo journalctl -u lustfulservicebot -n 100
```

#### 9.2 更新部署
```bash
# 停止服务
sudo systemctl stop lustfulservicebot

# 更新代码
cd /opt/lustfulservicebot
git pull  # 或上传新文件

# 更新依赖（如有需要）
source venv/bin/activate
pip install -r requirements.txt

# 数据库和初始数据会在启动时自动处理

# 重启服务
sudo systemctl start lustfulservicebot
```

### 10. 故障排除

#### 10.1 常见问题

**服务无法启动**：
```bash
# 检查配置文件
cat .env

# 检查Python环境
source venv/bin/activate
python -c "import aiogram; print('OK')"

# 手动运行测试
python -m app.bot
```

**数据库问题**：
```bash
# 删除数据库文件，重启时会自动重新创建
rm -f db/bot.db
python -m app.bot
```

**权限问题**：
```bash
# 修复文件权限
sudo chown -R your_username:your_username /opt/lustfulservicebot
chmod -R 755 /opt/lustfulservicebot
```

#### 10.2 性能优化

**内存优化**：
- 定期重启服务释放内存
- 配置日志轮转避免日志文件过大
- 清理旧的数据库记录

**网络优化**：
- 使用CDN加速（如适用）
- 配置适当的超时设置
- 监控网络连接状态

## 📞 技术支持

如果在部署过程中遇到问题，请检查：

1. **日志文件**：`/opt/lustfulservicebot/logs/`
2. **系统日志**：`sudo journalctl -u lustfulservicebot`
3. **配置文件**：确保 `.env` 文件配置正确
4. **网络连接**：确保服务器可以访问Telegram API

## 🔄 更新日志

- **v1.0.0**：初始版本，包含所有核心功能
- 代发消息系统
- 回复追踪功能
- 用户管理系统
- 反馈处理功能
- 系统配置管理