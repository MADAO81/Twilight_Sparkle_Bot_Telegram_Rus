# bot/services/weather_service.py
"""
Сервис погоды для бота Сумеречная Искорка.
Использует Open-Meteo (бесплатно, без ключа).

Автор: MADAO81
Версия: 1.0
"""

import logging
from typing import Optional, Dict, Tuple
import aiohttp
from bot.config import Config

logger = logging.getLogger(__name__)


class WeatherService:
    """
    Сервис погоды с использованием Open-Meteo API (без ключа).
    """

    def __init__(self):
        self.default_lat = Config.DEFAULT_LAT
        self.default_lon = Config.DEFAULT_LON
        self.base_url = "https://api.open-meteo.com/v1/forecast"
        self.geo_url = "https://geocoding-api.open-meteo.com/v1/search"

    async def get_weather(self, lat: Optional[float] = None, lon: Optional[float] = None) -> Optional[Dict]:
        """Получает текущую погоду по координатам."""
        if lat is None or lon is None:
            lat = self.default_lat
            lon = self.default_lon

        try:
            params = {
                "latitude": lat,
                "longitude": lon,
                "current_weather": "true",
                "timezone": "Europe/Moscow",
                "forecast_days": 1
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                        self.base_url,
                        params=params,
                        timeout=10.0
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_weather(data, lat, lon)
                    else:
                        logger.error(f"❌ Ошибка Open-Meteo: {response.status}")
                        return None

        except aiohttp.ClientError as e:
            logger.error(f"❌ Ошибка соединения: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Ошибка при получении погоды: {e}")
            return None

    async def get_weather_by_city(self, city: str) -> Optional[Dict]:
        """Получает погоду по названию города."""
        if not city:
            return await self.get_weather()

        coords = await self.get_city_coordinates(city)
        if not coords:
            logger.warning(f"⚠️ Город не найден: {city}")
            return None

        lat, lon = coords
        weather = await self.get_weather(lat, lon)
        if weather:
            weather["city_name"] = city
        return weather

    async def get_city_coordinates(self, city: str) -> Optional[Tuple[float, float]]:
        """Получает координаты города через Open-Meteo Geocoding API."""
        try:
            params = {
                "name": city,
                "count": 1,
                "language": "ru",
                "format": "json"
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                        self.geo_url,
                        params=params,
                        timeout=10.0
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = data.get("results", [])
                        if results and len(results) > 0:
                            lat = results[0].get("latitude")
                            lon = results[0].get("longitude")
                            if lat and lon:
                                logger.info(f"🌍 Найдены координаты для {city}: {lat}, {lon}")
                                return (lat, lon)
                    logger.warning(f"⚠️ Город '{city}' не найден")
                    return None

        except Exception as e:
            logger.error(f"❌ Ошибка при поиске города: {e}")
            return None

    def _parse_weather(self, data: Dict, lat: float, lon: float) -> Dict:
        """Парсит данные о погоде из Open-Meteo."""
        try:
            current = data.get("current_weather", {})

            weather_code = current.get("weathercode", 0)
            temperature = current.get("temperature", 0)
            wind_speed = current.get("windspeed", 0)

            weather = {
                "temperature": temperature,
                "feels_like": temperature,
                "humidity": 0,
                "pressure": 0,
                "wind_speed": wind_speed,
                "condition": self._get_condition(weather_code),
                "description": self._translate_condition(weather_code),
                "city_name": "Ворсино" if lat == self.default_lat and lon == self.default_lon else "Неизвестный город",
                "country": "",
                "is_bad": self._is_bad_weather(weather_code)
            }

            return weather

        except Exception as e:
            logger.error(f"❌ Ошибка парсинга погоды: {e}")
            return {
                "temperature": 0,
                "feels_like": 0,
                "humidity": 0,
                "pressure": 750,
                "wind_speed": 0,
                "condition": "clear",
                "description": "неизвестно",
                "city_name": "Неизвестный город",
                "country": "",
                "is_bad": False
            }

    def _get_condition(self, code: int) -> str:
        """Преобразует код погоды Open-Meteo в строку."""
        if code == 0:
            return "clear"
        elif code in [1, 2, 3]:
            return "cloudy"
        elif code in [45, 48]:
            return "fog"
        elif code in [51, 53, 55, 56, 57]:
            return "drizzle"
        elif code in [61, 63, 65, 66, 67, 80, 81, 82]:
            return "rain"
        elif code in [71, 73, 75, 77, 85, 86]:
            return "snow"
        elif code in [95, 96, 99]:
            return "thunderstorm"
        else:
            return "clear"

    def _translate_condition(self, code: int) -> str:
        """Переводит код погоды на русский."""
        conditions = {
            "clear": "ясно",
            "cloudy": "облачно",
            "fog": "туман",
            "drizzle": "морось",
            "rain": "дождь",
            "snow": "снег",
            "thunderstorm": "гроза"
        }
        condition = self._get_condition(code)
        return conditions.get(condition, "неизвестно")

    def _is_bad_weather(self, code: int) -> bool:
        """Определяет, плохая ли погода."""
        bad_codes = [45, 48, 51, 53, 55, 56, 57, 61, 63, 65, 66, 67,
                     71, 73, 75, 77, 80, 81, 82, 85, 86, 95, 96, 99]
        return code in bad_codes

    def is_bad_weather(self, weather_data: Optional[Dict]) -> bool:
        """Проверяет, плохая ли погода."""
        if not weather_data:
            return False
        return weather_data.get("is_bad", False)

    def get_weather_text(self, weather_data: Optional[Dict], city_display: Optional[str] = None) -> str:
        """Возвращает текстовое описание погоды."""
        if not weather_data:
            return "🌤️ Погода: неизвестно"

        temp = weather_data.get("temperature", 0)
        description = weather_data.get("description", "неизвестно")
        wind = weather_data.get("wind_speed", 0)

        city = city_display if city_display else weather_data.get("city_name", "неизвестном городе")

        emoji = "☀️" if not weather_data.get("is_bad", False) else "🌧️"

        return f"{emoji} В {city} сейчас {description}, {temp}°C, ветер {wind} м/с"