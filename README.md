# 桜色服务助手 🌸

一个功能完整的Telegram机器人，专为服务管理和用户交互而设计。

## ✨ 功能特性

### 🎯 核心功能

- **代发消息系统** - 管理员可向指定用户发送消息
- **回复追踪** - 自动监听用户回复并通知管理员
- **用户管理** - 完整的用户角色和权限系统
- **反馈系统** - 用户反馈收集和处理
- **内容管理** - 求片、投稿等内容管理功能

### 🛠️ 管理功能

- **多级权限** - 超管、管理员、普通用户三级权限
- **系统设置** - 灵活的功能开关和配置管理
- **数据统计** - 用户活跃度和系统使用统计
- **日志记录** - 完整的操作日志和错误追踪

### 💬 交互功能

- **智能回复** - 支持HTML格式的富文本消息
- **按钮交互** - 直观的内联键盘操作
- **文件处理** - 支持图片、文档等多媒体内容
- **状态管理** - 智能的对话状态跟踪

## 🚀 快速开始

### 环境要求

- Python 3.12+
- Telegram Bot Token
- SQLite数据库（默认）

### 安装步骤

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd lustfulservicebot
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **配置环境**
   ```bash
   cp .env.example .env
   # 编辑 .env 文件，填入你的配置
   ```

4. **启动机器人**
   ```bash
   python -m app.bot
   ```
   
   首次启动时会自动创建数据库表和初始数据。

## 📋 配置说明

### 环境变量

创建 `.env` 文件并配置以下变量：

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
```

### 获取Bot Token

1. 在Telegram中找到 [@BotFather](https://t.me/BotFather)
2. 发送 `/newbot` 创建新机器人
3. 按提示设置机器人名称和用户名
4. 获取Bot Token并填入配置文件

### 获取用户ID

1. 在Telegram中找到 [@userinfobot](https://t.me/userinfobot)
2. 发送任意消息获取你的用户ID
3. 将用户ID填入 `SUPERADMIN_ID`

## 🎮 使用指南

### 管理员命令

#### 代发消息
- `/su [用户ID] [消息内容]` - 发送消息给指定用户
- `/sc [频道ID] [消息内容]` - 发送消息到频道
- `/sg [群组ID] [消息内容]` - 发送消息到群组

#### 回复管理
- `/replies` 或 `/r` - 查看用户回复
- `/history [用户ID]` 或 `/h [用户ID]` - 查看对话历史
- `/mark_read [记录ID]` 或 `/mr [记录ID]` - 标记回复为已读

#### 系统管理
- `/add_admin [用户ID]` - 添加管理员
- `/demote [用户ID]` - 移除管理员权限
- `/view_settings` - 查看系统设置
- `/toggle_feature [功能名]` - 切换功能开关

### 用户命令

- `/start` - 启动机器人
- `/help` - 获取帮助信息
- 直接发送消息进行反馈

## 🏗️ 项目结构

```
lustfulservicebot/
├── app/                    # 应用主目录
│   ├── bot.py             # 机器人入口文件
│   ├── config/            # 配置文件
│   ├── database/          # 数据库模型和操作
│   ├── handlers/          # 消息处理器
│   │   ├── admins/        # 管理员功能
│   │   └── users/         # 用户功能
│   ├── middlewares/       # 中间件
│   ├── buttons/           # 按钮和键盘
│   └── utils/             # 工具函数
├── db/                    # 数据库文件
├── logs/                  # 日志文件
├── docs/                  # 文档
├── requirements.txt       # Python依赖
├── create_tables.py       # 数据库初始化
└── README.md             # 项目说明
```

## 🔧 开发指南

### 添加新功能

1. **创建处理器**
   ```python
   # app/handlers/users/new_feature.py
   from aiogram import Router, types
   
   router = Router()
   
   @router.message()
   async def handle_new_feature(msg: types.Message):
       await msg.reply("新功能响应")
   ```

2. **注册路由**
   ```python
   # app/handlers/users/__init__.py
   from .new_feature import router as new_feature_router
   
   users_routers = [
       # ... 其他路由
       new_feature_router,
   ]
   ```

### 数据库操作

```python
# 使用异步数据库操作
from app.database.db import AsyncSessionLocal

async def example_db_operation():
    async with AsyncSessionLocal() as session:
        # 数据库操作
        await session.commit()
```

### 日志记录

```python
from loguru import logger

logger.info("信息日志")
logger.warning("警告日志")
logger.error("错误日志")
```

## 📊 功能模块

### 代发消息系统
- ✅ 发送消息给用户/群组/频道
- ✅ 消息记录和追踪
- ✅ 回复自动通知
- ✅ 对话历史管理
- ✅ 已读状态管理

### 用户管理系统
- ✅ 多级权限控制
- ✅ 用户信息收集
- ✅ 活跃度统计
- ✅ 权限动态分配

### 反馈系统
- ✅ 用户反馈收集
- ✅ 管理员回复
- ✅ 反馈状态跟踪
- ✅ 分类管理

### 内容管理
- ✅ 求片功能
- ✅ 内容投稿
- ✅ 审核流程
- ✅ 分类管理

## 🚀 部署

详细的部署指南请参考 [DEPLOYMENT.md](DEPLOYMENT.md)

### Docker部署（推荐）

```bash
# 构建镜像
docker build -t lustfulservicebot .

# 运行容器
docker run -d --name bot \
  -v $(pwd)/.env:/app/.env \
  -v $(pwd)/db:/app/db \
  -v $(pwd)/logs:/app/logs \
  lustfulservicebot
```

### 系统服务部署

```bash
# 创建systemd服务
sudo cp lustfulservicebot.service /etc/systemd/system/
sudo systemctl enable lustfulservicebot
sudo systemctl start lustfulservicebot
```

## 📝 更新日志

### v1.0.0 (2025-09-06)
- ✨ 初始版本发布
- ✨ 代发消息系统
- ✨ 回复追踪功能
- ✨ 用户管理系统
- ✨ 反馈处理功能
- ✨ 系统配置管理
- 🐛 修复带图片消息编辑错误
- 🐛 修复路由优先级问题
- 🐛 修复数据库异步操作

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个项目！

### 开发流程

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🙏 致谢

- [aiogram](https://github.com/aiogram/aiogram) - 优秀的Telegram Bot框架
- [SQLAlchemy](https://sqlalchemy.org/) - 强大的ORM框架
- [loguru](https://github.com/Delgan/loguru) - 简洁的日志库

## 📞 支持

如果你觉得这个项目有用，请给它一个 ⭐️

如有问题或建议，请通过以下方式联系：

- 创建 [Issue](../../issues)
- 发送邮件到项目维护者

---

**桜色服务助手** - 让Telegram机器人管理变得简单高效 🌸
