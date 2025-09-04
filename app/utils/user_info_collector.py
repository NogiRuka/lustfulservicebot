import re
import asyncio
import aiohttp
from typing import Dict, Optional
from loguru import logger
from datetime import datetime


class UserInfoCollector:
    """用户信息收集器"""
    
    def __init__(self):
        self.ip_api_url = "http://ip-api.com/json/{}"
        self.user_agent_patterns = {
            'mobile': r'(Mobile|Android|iPhone|iPad|iPod|BlackBerry|Windows Phone)',
            'desktop': r'(Windows NT|Macintosh|Linux)',
            'tablet': r'(iPad|Android.*Tablet)',
            'bot': r'(bot|crawler|spider|scraper)'
        }
        
    async def get_ip_location(self, ip_address: str) -> Dict[str, Optional[str]]:
        """
        通过IP地址获取地理位置信息
        """
        if not ip_address or ip_address in ['127.0.0.1', 'localhost']:
            return {}
            
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.ip_api_url.format(ip_address)) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('status') == 'success':
                            return {
                                'country': data.get('country'),
                                'country_code': data.get('countryCode'),
                                'region': data.get('regionName'),
                                'city': data.get('city'),
                                'timezone': data.get('timezone'),
                                'latitude': str(data.get('lat')) if data.get('lat') else None,
                                'longitude': str(data.get('lon')) if data.get('lon') else None
                            }
        except Exception as e:
            logger.error(f"获取IP地理位置失败: {e}")
        
        return {}
    
    def parse_user_agent(self, user_agent: str) -> Dict[str, Optional[str]]:
        """
        解析用户代理字符串
        """
        if not user_agent:
            return {}
            
        device_type = 'unknown'
        platform = 'unknown'
        
        # 检测设备类型
        for device, pattern in self.user_agent_patterns.items():
            if re.search(pattern, user_agent, re.IGNORECASE):
                device_type = device
                break
        
        # 检测平台
        if 'Windows NT' in user_agent:
            platform = 'Windows'
        elif 'Macintosh' in user_agent or 'Mac OS' in user_agent:
            platform = 'macOS'
        elif 'Linux' in user_agent:
            platform = 'Linux'
        elif 'Android' in user_agent:
            platform = 'Android'
        elif 'iPhone' in user_agent or 'iPad' in user_agent:
            platform = 'iOS'
        
        # 提取版本信息
        app_version = None
        version_match = re.search(r'Telegram/(\d+\.\d+)', user_agent)
        if version_match:
            app_version = version_match.group(1)
        
        return {
            'device_type': device_type,
            'platform': platform,
            'app_version': app_version
        }
    
    def extract_telegram_info(self, telegram_user) -> Dict[str, any]:
        """
        从Telegram用户对象提取详细信息
        """
        if not telegram_user:
            return {}
            
        return {
            'language_code': getattr(telegram_user, 'language_code', None),
            'is_bot': getattr(telegram_user, 'is_bot', False),
            'is_premium': getattr(telegram_user, 'is_premium', False),
            'added_to_attachment_menu': getattr(telegram_user, 'added_to_attachment_menu', False),
            'can_join_groups': getattr(telegram_user, 'can_join_groups', True),
            'can_read_all_group_messages': getattr(telegram_user, 'can_read_all_group_messages', False),
            'supports_inline_queries': getattr(telegram_user, 'supports_inline_queries', False)
        }
    
    async def collect_user_info(self, telegram_user, ip_address: str = None, user_agent: str = None) -> Dict[str, any]:
        """
        收集完整的用户信息
        """
        user_info = {
            'basic_info': {
                'chat_id': telegram_user.id,
                'full_name': telegram_user.full_name,
                'username': telegram_user.username,
            },
            'telegram_info': self.extract_telegram_info(telegram_user),
            'network_info': {
                'ip_address': ip_address,
                'user_agent': user_agent
            }
        }
        
        # 获取地理位置信息
        if ip_address:
            location_info = await self.get_ip_location(ip_address)
            user_info['location_info'] = location_info
        
        # 解析设备信息
        if user_agent:
            device_info = self.parse_user_agent(user_agent)
            user_info['device_info'] = device_info
        
        return user_info
    
    def analyze_user_behavior(self, user_data: Dict) -> Dict[str, any]:
        """
        分析用户行为模式
        """
        current_hour = datetime.now().hour
        
        behavior_analysis = {
            'current_active_hour': current_hour,
            'session_start': datetime.now(),
        }
        
        # 可以根据历史数据进行更复杂的分析
        # 这里只是基础示例
        
        return behavior_analysis
    
    def get_privacy_settings(self, user_preferences: Dict = None) -> Dict[str, bool]:
        """
        获取用户隐私设置
        """
        default_settings = {
            'allow_location_tracking': True,
            'allow_analytics': True,
            'allow_ip_logging': True,
            'allow_device_tracking': True
        }
        
        if user_preferences:
            default_settings.update(user_preferences)
        
        return default_settings


# 全局实例
user_info_collector = UserInfoCollector()


# 便捷函数
async def collect_and_store_user_info(telegram_user, ip_address: str = None, user_agent: str = None):
    """
    收集并存储用户信息的便捷函数
    """
    from app.database.users import add_user, update_user_location
    
    try:
        # 收集用户信息
        user_info = await user_info_collector.collect_user_info(telegram_user, ip_address, user_agent)
        
        # 准备设备信息
        device_info = user_info.get('device_info', {})
        telegram_info = user_info.get('telegram_info', {})
        
        # 添加或更新用户基础信息
        await add_user(
            chat_id=telegram_user.id,
            full_name=telegram_user.full_name,
            username=telegram_user.username,
            language_code=telegram_info.get('language_code'),
            is_bot=telegram_info.get('is_bot', False),
            is_premium=telegram_info.get('is_premium', False),
            ip_address=ip_address,
            user_agent=user_agent,
            device_info=device_info
        )
        
        # 更新地理位置信息
        location_info = user_info.get('location_info', {})
        if location_info:
            await update_user_location(telegram_user.id, location_info)
        
        logger.info(f"用户信息收集完成: {telegram_user.username} ({telegram_user.id})")
        return True
        
    except Exception as e:
        logger.error(f"收集用户信息失败: {e}")
        return False