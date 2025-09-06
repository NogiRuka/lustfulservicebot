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

## ✨ **用户功能**

### 💬 **反馈系统**
- ✅ 用户可以直接发送消息进行反馈
- ✅ 管理员会及时回复用户反馈
- ✅ 支持多种反馈类型（建议、问题、投诉等）

### 📝 **内容功能**
- ✅ 求片功能 - 用户可以请求想要的影片资源
- ✅ 内容投稿 - 用户可以分享优质内容
- ✅ 分类浏览 - 按类型查找感兴趣的内容

### 🎮 **交互功能**
- ✅ 简洁的用户面板和按钮操作
- ✅ 智能的命令响应
- ✅ 友好的使用帮助

### 📊 **个人功能**
- ✅ 查看个人信息和使用统计
- ✅ 查看服务器状态信息
- ✅ 清空聊天记录

## 🎯 **使用指南**

### 📱 **开始使用**
1. 发送 `/start` 启动机器人
2. 点击按钮或发送命令进行操作
3. 直接发送消息即可进行反馈

### 🔘 **主要按钮**
- **我的信息** - 查看个人资料
- **服务器信息** - 查看系统状态
- **其他功能** - 更多实用功能
- **帮助** - 获取使用帮助

### 💡 **使用提示**
- 所有功能都通过简单的按钮操作
- 有问题可以直接发送消息反馈
- 管理员会及时处理用户请求

---

**感谢使用桜色服务助手！我们致力于为您提供最好的服务体验。** 🎉✨🚀"""

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