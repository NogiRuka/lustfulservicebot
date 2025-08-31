from datetime import datetime, timedelta

def humanize_time(dt: datetime) -> str:
    """将时间转换为人性化显示"""
    now = datetime.now()
    diff = now - dt
    
    if diff.days > 0:
        if diff.days == 1:
            return "昨天"
        elif diff.days < 7:
            return f"{diff.days}天前"
        elif diff.days < 30:
            weeks = diff.days // 7
            return f"{weeks}周前"
        else:
            return dt.strftime("%m月%d日")
    
    hours = diff.seconds // 3600
    if hours > 0:
        return f"{hours}小时前"
    
    minutes = diff.seconds // 60
    if minutes > 0:
        return f"{minutes}分钟前"
    
    return "刚刚"

def get_status_text(status: str) -> str:
    """将状态转换为中文显示"""
    status_map = {
        "pending": "待审核",
        "approved": "已通过", 
        "rejected": "已拒绝",
        "processing": "处理中",
        "resolved": "已解决"
    }
    return status_map.get(status, status)