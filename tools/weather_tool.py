"""天气工具（基于 OpenWeatherMap API）"""
import requests


class WeatherTool:
    """OpenWeatherMap 天气工具"""

    def __init__(self, api_key: str):
        """
        初始化

        参数:
            api_key: OpenWeatherMap API key (免费注册: https://openweathermap.org/api)
        """
        self.api_key = api_key
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"

    def execute(self, city: str = "New York", country_code: str = "US") -> dict:
        """
        获取天气信息

        参数:
            city: 城市名（英文）
            country_code: 国家代码（US, GB, JP, etc.）

        返回:
            {
                "city": "New York",
                "country": "US",
                "weather": "clear sky",
                "temperature": "25°C",
                "feels_like": "27°C",
                "humidity": "60%",
                "formatted": "clear sky, 25°C"
            }
        """
        if not self.api_key:
            return {
                "error": "未配置 weather_api_key",
                "formatted": "unknown"
            }

        params = {
            "q": f"{city},{country_code}",
            "appid": self.api_key,
            "units": "metric",  # 摄氏度
            "lang": "en"
        }

        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("cod") != 200:
                return {
                    "error": f"获取天气失败: {data.get('message', 'unknown error')}",
                    "formatted": "unknown"
                }

            return {
                "city": data["name"],
                "country": data["sys"]["country"],
                "weather": data["weather"][0]["description"],
                "temperature": f"{int(data['main']['temp'])}°C",
                "feels_like": f"{int(data['main']['feels_like'])}°C",
                "humidity": f"{data['main']['humidity']}%",
                "formatted": f"{data['weather'][0]['description']}, {int(data['main']['temp'])}°C"
            }

        except requests.RequestException as e:
            return {
                "error": f"网络请求失败: {str(e)}",
                "formatted": "unknown"
            }
        except Exception as e:
            return {
                "error": f"解析天气数据失败: {str(e)}",
                "formatted": "unknown"
            }
