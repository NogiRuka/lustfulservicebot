# 调试系统使用指南

## 概述

本项目集成了完整的调试系统，可以帮助开发者在开发过程中跟踪审核流程的每一个步骤，特别是主消息ID的跟踪和管理。

## 调试模式

系统支持三种调试模式：

### 1. 开发模式 (development)
- **默认模式**，显示所有调试信息
- 适用于本地开发和调试
- 显示详细的函数进入/退出信息

### 2. 测试模式 (testing)
- 显示关键调试信息，隐藏详细信息
- 适用于测试环境
- 不显示函数进入/退出和状态详情

### 3. 生产模式 (production)
- **禁用所有调试信息**
- 适用于生产环境
- 只保留错误日志

## 配置方法

### 环境变量配置

```bash
# 设置调试模式
export DEBUG_MODE=development  # 开发模式
export DEBUG_MODE=testing      # 测试模式
export DEBUG_MODE=production   # 生产模式
```

### 代码配置

```python
from app.config.debug_config import set_debug_mode, enable_debug, disable_debug

# 设置特定模式
set_debug_mode('development')

# 快捷方法
enable_debug()   # 启用开发模式
disable_debug()  # 切换到生产模式
set_testing_mode()  # 切换到测试模式
```

## 调试信息类型

### 1. 主消息ID跟踪 📍
跟踪用户start命令创建的主消息ID在整个审核流程中的传递和使用：

```
🔍 DEBUG [DEVELOPMENT]: 📍 主消息ID跟踪 | action=设置主消息ID | old_id=None | new_id=1001 | source=审核中心主面板
```

### 2. 媒体消息跟踪 📱
跟踪媒体消息的发送、删除和管理：

```
🔍 DEBUG [DEVELOPMENT]: 📱 媒体消息跟踪 | action=发送媒体消息 | media_count=3 | media_ids=[1002, 1003, 1004]
```

### 3. 审核流程跟踪 🔄
跟踪审核流程的每个步骤：

```
🔍 DEBUG [DEVELOPMENT]: 🔄 审核流程: 开始处理求片通过留言 | request_id=123
```

### 4. 消息信息跟踪
显示回调查询的详细信息：

```
🔍 DEBUG [DEVELOPMENT]: 当前回调消息消息信息 | message_id=1001 | chat_id=123456 | user_id=789 | callback_data=approve_movie_note_123
```

### 5. 状态信息跟踪
显示FSM状态的详细信息：

```
🔍 DEBUG [DEVELOPMENT]: 进入前状态信息 | current_state=None | main_message_id=1001 | message_id=1001 | sent_media_count=3
```

### 6. 函数执行跟踪 🚀
跟踪函数的进入和退出：

```
🔍 DEBUG [DEVELOPMENT]: 🚀 进入函数: 审核留言-通过求片
🔍 DEBUG [DEVELOPMENT]: ✅ 函数完成: 审核留言-通过求片
```

### 7. 错误信息跟踪 ❌
详细的错误信息和上下文：

```
🔍 DEBUG [DEVELOPMENT]: ❌ 错误 | error_type=媒体消息发送失败 | error_msg=message to edit not found | item_id=123
```

## 关键调试点

### 审核流程关键节点

1. **进入审核中心**
   - 主消息ID设置
   - 权限检查
   - 媒体消息清理

2. **进入审核列表**
   - 主消息ID更新
   - 媒体消息发送
   - 分页处理

3. **审核留言操作**
   - 主消息ID保持
   - 状态数据管理
   - 消息编辑

4. **确认审核**
   - 审核执行
   - 通知发送
   - 媒体消息清理
   - 返回处理

## 实际使用示例

### 开发时启用调试

```python
# 在开发环境中
from app.config.debug_config import enable_debug
enable_debug()

# 现在所有审核操作都会显示详细的调试信息
```

### 生产环境禁用调试

```python
# 在生产环境中
from app.config.debug_config import disable_debug
disable_debug()

# 现在只会显示错误信息，不会有调试输出
```

### 查看特定功能的调试信息

```python
from app.config.debug_config import should_show_feature

# 检查是否应该显示主消息跟踪
if should_show_feature('main_message_tracking'):
    print("主消息跟踪已启用")
```

## 调试信息解读

### 主消息ID问题排查

当出现"message to edit not found"错误时，查看调试日志：

1. 查找主消息ID设置日志
2. 确认主消息ID在流程中的传递
3. 检查是否使用了正确的消息ID进行编辑

示例日志分析：
```
🔍 DEBUG: 📍 主消息ID跟踪 | action=审核中心设置主消息ID | old_id=None | new_id=1001
🔍 DEBUG: 📍 主消息ID跟踪 | action=设置主消息ID | old_id=1001 | new_id=1001 | source=保存的ID
🔍 DEBUG: 🔄 审核流程: 准备编辑消息显示留言输入界面 | target_message_id=1001
```

### 媒体消息管理排查

查看媒体消息的生命周期：

```
🔍 DEBUG: 📱 媒体消息跟踪 | action=开始发送媒体消息 | total_items=5
🔍 DEBUG: 📱 媒体消息跟踪 | action=媒体消息ID已记录 | message_ids=[1002] | total_sent=1
🔍 DEBUG: 📱 媒体消息跟踪 | action=清理媒体消息 | message_ids=[1002, 1003, 1004]
```

## 文件日志功能

### 自动文件日志

调试系统支持将调试信息实时写入文件，方便查看和分析：

**文件日志配置**:
- **开发模式**: 自动写入 `logs/debug.log`，最大10MB，保留5个备份
- **测试模式**: 自动写入 `logs/debug_test.log`，最大5MB，保留3个备份
- **生产模式**: 不写入文件日志

**日志文件特性**:
- ✅ 实时写入，无需重启
- ✅ 自动轮转，避免文件过大
- ✅ 压缩备份，节省磁盘空间
- ✅ UTF-8编码，支持中文

### 手动控制文件日志

```python
from app.utils.debug_utils import enable_file_logging, disable_file_logging, get_debug_log_file

# 启用文件日志
enable_file_logging()

# 启用文件日志并指定路径
enable_file_logging('custom_logs/my_debug.log')

# 禁用文件日志
disable_file_logging()

# 获取当前日志文件路径
log_file = get_debug_log_file()
print(f"当前日志文件: {log_file}")
```

### 日志查看工具

项目提供了专用的日志查看工具 `tools/debug_log_viewer.py`：

**查看最近的日志**:
```bash
python tools/debug_log_viewer.py --tail 100
```

**实时跟踪日志**:
```bash
python tools/debug_log_viewer.py --follow
```

**过滤特定内容**:
```bash
python tools/debug_log_viewer.py --filter "主消息ID"
python tools/debug_log_viewer.py --filter "审核流程"
```

**查看调试配置**:
```bash
python tools/debug_log_viewer.py --info
```

**指定日志文件**:
```bash
python tools/debug_log_viewer.py --file logs/debug.log --tail 50
```

### 日志文件示例

```
2025-09-06 06:33:44.770 | DEBUG    | app.utils.debug_utils:debug_log:21 - 🔍 DEBUG [DEVELOPMENT]: 🚀 进入函数: 审核中心入口
2025-09-06 06:33:44.771 | DEBUG    | app.utils.debug_utils:debug_log:21 - 🔍 DEBUG [DEVELOPMENT]: 🔄 审核流程: 进入审核中心
2025-09-06 06:33:44.772 | DEBUG    | app.utils.debug_utils:debug_log:21 - 🔍 DEBUG [DEVELOPMENT]: 📍 主消息ID跟踪 | action=审核中心设置主消息ID | old_id=None | new_id=1001
```

## 性能考虑

- 调试信息只在启用时才会执行
- 生产模式下几乎没有性能影响
- 开发模式下会有轻微的日志开销
- 文件日志使用异步写入，对性能影响最小

## 最佳实践

1. **开发时**：使用development模式，查看所有调试信息
2. **测试时**：使用testing模式，关注关键流程
3. **生产时**：使用production模式，只保留错误日志
4. **问题排查**：临时启用development模式进行详细分析

## 环境变量设置

在不同环境中设置相应的环境变量：

```bash
# .env 文件或环境配置
DEBUG_MODE=development  # 本地开发
DEBUG_MODE=testing      # 测试环境
DEBUG_MODE=production   # 生产环境
```

这样可以确保在不同环境中自动使用合适的调试级别。