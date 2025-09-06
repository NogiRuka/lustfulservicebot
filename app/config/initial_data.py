#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
桜色服务助手 - 初始数据配置
包含首次启动时需要插入的初始数据配置
"""

# ===== 初始开发日志配置 =====
INITIAL_VERSION = "v1.0.0"
INITIAL_CHANGELOG_TITLE = "🎉 桜色服务助手首次发布"
INITIAL_CHANGELOG_TYPE = "feature"

# ===== 初始开发日志内容 =====
INITIAL_CHANGELOG_CONTENT = """🌸 **桜色服务助手 v1.0.0 正式发布！**

## ✨ **核心功能**

### 🎯 **代发消息系统**
- ✅ 支持发送消息给指定用户 (`/su`)
- ✅ 支持发送消息到频道 (`/sc`)
- ✅ 支持发送消息到群组 (`/sg`)
- ✅ 智能编辑/回复降级机制
- ✅ 完整的消息记录和追踪

### 📬 **回复追踪系统**
- ✅ 自动监听用户回复
- ✅ 实时通知所有管理员
- ✅ 完整的对话历史记录
- ✅ 已读状态管理
- ✅ 反馈回复特殊处理

### 👥 **用户管理系统**
- ✅ 三级权限控制（用户/管理员/超管）
- ✅ 动态权限分配
- ✅ 用户信息自动收集
- ✅ 活跃度统计

### 💬 **反馈系统**
- ✅ 用户反馈收集
- ✅ 管理员回复功能
- ✅ 反馈状态跟踪
- ✅ 分类管理

### 📝 **内容管理**
- ✅ 求片功能
- ✅ 内容投稿
- ✅ 审核流程
- ✅ 分类管理
- ✅ 状态跟踪

### 🛠️ **系统管理**
- ✅ 灵活的系统设置
- ✅ 功能开关控制
- ✅ 图片库管理
- ✅ 开发日志管理
- ✅ 完整的日志记录

## 🔧 **技术特性**

### 🏗️ **架构设计**
- ✅ 基于 aiogram 3.x 异步框架
- ✅ 模块化路由设计
- ✅ 中间件系统
- ✅ 状态管理

### 🗄️ **数据库**
- ✅ SQLAlchemy ORM
- ✅ 异步数据库操作
- ✅ 完整的数据模型
- ✅ 自动表创建

### 📊 **日志系统**
- ✅ loguru 日志框架
- ✅ 文件轮转
- ✅ 多级别日志
- ✅ 调试支持

### 🔒 **安全性**
- ✅ 权限验证
- ✅ 角色检查
- ✅ 操作日志
- ✅ 错误处理

## 🐛 **修复的问题**

### 🔄 **路由优化**
- 🐛 修复命令消息优先级问题
- 🐛 调整路由注册顺序
- 🐛 移除冲突的消息处理器

### 📱 **消息处理**
- 🐛 修复带图片消息编辑错误
- 🐛 实现智能降级机制
- 🐛 优化消息格式

### 🗄️ **数据库**
- 🐛 修复异步连接问题
- 🐛 优化数据库操作
- 🐛 完善错误处理

### 🎯 **功能完善**
- 🐛 修复回复追踪器角色检查
- 🐛 添加反馈回复处理
- 🐛 优化用户体验

## 🚀 **部署支持**

### 📋 **文档**
- ✅ 完整的 README.md
- ✅ 详细的部署指南
- ✅ API 文档
- ✅ 开发指南

### 🐳 **容器化**
- ✅ Dockerfile 配置
- ✅ docker-compose.yml
- ✅ 健康检查
- ✅ 多服务支持

### ⚙️ **系统服务**
- ✅ systemd 服务配置
- ✅ 自动重启
- ✅ 日志管理
- ✅ 安全设置

### 💾 **备份**
- ✅ 自动备份脚本
- ✅ 定时任务支持
- ✅ 数据压缩
- ✅ 清理策略

## 🎯 **使用统计**

- **代码行数**: 5000+ 行
- **功能模块**: 15+ 个
- **命令数量**: 30+ 个
- **数据表**: 10+ 个

## 💡 **下一步计划**

- 🔄 性能优化
- 📊 数据分析功能
- 🌐 Web 管理界面
- 📱 移动端适配
- 🔌 插件系统

---

**感谢使用桜色服务助手！这是一个里程碑式的版本，标志着项目的正式发布。** 🎉✨🚀"""

# ===== 初始系统设置配置 =====
INITIAL_SYSTEM_SETTINGS = [
    {
        "setting_key": "user_feedback_enabled",
        "setting_value": "true",
        "setting_type": "boolean",
        "description": "是否启用用户反馈功能"
    },
    {
        "setting_key": "movie_requests_enabled",
        "setting_value": "true",
        "setting_type": "boolean",
        "description": "是否启用求片功能"
    },
    {
        "setting_key": "content_submission_enabled",
        "setting_value": "true",
        "setting_type": "boolean",
        "description": "是否启用内容投稿功能"
    },
    {
        "setting_key": "max_file_size",
        "setting_value": "50MB",
        "setting_type": "string",
        "description": "最大文件上传大小"
    },
    {
        "setting_key": "auto_backup_enabled",
        "setting_value": "true",
        "setting_type": "boolean",
        "description": "是否启用自动备份"
    }
]

# ===== 初始分类配置 =====
INITIAL_CATEGORIES = [
    {
        "name": "动作片",
        "description": "动作、冒险类电影",
        "sort_order": 1
    },
    {
        "name": "喜剧片",
        "description": "喜剧、搞笑类电影",
        "sort_order": 2
    },
    {
        "name": "剧情片",
        "description": "剧情、文艺类电影",
        "sort_order": 3
    },
    {
        "name": "科幻片",
        "description": "科幻、奇幻类电影",
        "sort_order": 4
    },
    {
        "name": "恐怖片",
        "description": "恐怖、惊悚类电影",
        "sort_order": 5
    },
    {
        "name": "爱情片",
        "description": "爱情、浪漫类电影",
        "sort_order": 6
    },
    {
        "name": "纪录片",
        "description": "纪录片、真实事件",
        "sort_order": 7
    },
    {
        "name": "动画片",
        "description": "动画、卡通类电影",
        "sort_order": 8
    }
]

def get_initial_changelog_data() -> dict:
    """获取初始开发日志数据"""
    return {
        "version": INITIAL_VERSION,
        "title": INITIAL_CHANGELOG_TITLE,
        "changelog_type": INITIAL_CHANGELOG_TYPE,
        "content": INITIAL_CHANGELOG_CONTENT
    }

def get_initial_system_settings() -> list:
    """获取初始系统设置数据"""
    return INITIAL_SYSTEM_SETTINGS.copy()

def get_initial_categories() -> list:
    """获取初始分类数据"""
    return INITIAL_CATEGORIES.copy()