"""
天气查询工具
支持 OpenWeatherMap API（免费套餐）
"""
import os
import requests
import logging

logger = logging.getLogger(__name__)


class WeatherTool:
    """天气查询工具"""

    name = 'weather'
    description = '查询指定城市的实时天气信息'

    BASE_URL = 'https://api.openweathermap.org/data/2.5/weather'

    @classmethod
    def query(cls, city: str) -> dict:
        """
        查询城市天气

        返回:
            {'success': True, 'data': {...}} 或 {'success': False, 'error': '...'}
        """
        api_key = os.getenv('WEATHER_API_KEY', '')
        if not api_key:
            return {
                'success': False,
                'error': '未配置 WEATHER_API_KEY 环境变量。请前往 https://openweathermap.org/api 获取免费 API Key',
            }

        try:
            params = {
                'q': city,
                'appid': api_key,
                'units': 'metric',  # 摄氏度
                'lang': 'zh_cn',
            }
            resp = requests.get(cls.BASE_URL, params=params, timeout=10)

            if resp.status_code == 200:
                data = resp.json()
                return {
                    'success': True,
                    'data': {
                        'city': data['name'],
                        'country': data.get('sys', {}).get('country', ''),
                        'temperature': round(data['main']['temp'], 1),
                        'feels_like': round(data['main']['feels_like'], 1),
                        'temp_min': round(data['main']['temp_min'], 1),
                        'temp_max': round(data['main']['temp_max'], 1),
                        'humidity': data['main']['humidity'],
                        'pressure': data['main']['pressure'],
                        'weather': data['weather'][0]['description'],
                        'weather_icon': data['weather'][0]['icon'],
                        'wind_speed': data['wind']['speed'],
                        'visibility': data.get('visibility', 'N/A'),
                    },
                }
            elif resp.status_code == 404:
                return {'success': False, 'error': f'未找到城市 "{city}" 的天气信息'}
            elif resp.status_code == 401:
                return {'success': False, 'error': 'API Key 无效或已过期'}
            else:
                return {'success': False, 'error': f'天气服务返回错误: {resp.status_code}'}

        except requests.Timeout:
            return {'success': False, 'error': '天气服务请求超时'}
        except Exception as e:
            logger.error(f'天气查询异常: {e}')
            return {'success': False, 'error': f'查询失败: {str(e)}'}
