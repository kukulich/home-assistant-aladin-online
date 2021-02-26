from datetime import datetime, timedelta
from homeassistant import core
from homeassistant.components.weather import (
	ATTR_CONDITION_CLEAR_NIGHT,
	ATTR_CONDITION_CLOUDY,
	ATTR_CONDITION_SUNNY,
	ATTR_CONDITION_PARTLYCLOUDY,
	ATTR_CONDITION_POURING,
)
from homeassistant.const import (
	CONF_LATITUDE,
	CONF_LONGITUDE,
	HTTP_OK,
)
from homeassistant.helpers import aiohttp_client
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt
import math
import pytz
from .const import (
	DOMAIN,
	LOGGER,
	URL,
)
from .errors import ServiceUnavailable
from types import MappingProxyType
from typing import List

DATA_TIME = "forecastTimeIso"
DATA_FORECAST_LENGTH = "forecastLength"
DATA_PARAMETERS = "parameterValues"
DATA_CONDITIONS = "weatherIconNames"
DATA_PARAMETER_HUMIDITY = "HUMIDITY"
DATA_PARAMETER_PRECIPITATION = "PRECIPITATION_TOTAL"
DATA_PARAMETER_PRESSURE = "PRESSURE"
DATA_PARAMETER_TEMPERATURE = "TEMPERATURE"
DATA_PARAMETER_WIND_DIRECTION = "WIND_DIRECTION"
DATA_PARAMETER_WIND_SPEED = "WIND_SPEED"

class AladinActualWeather:

	def __init__(self, condition: str, temperature: float, pressure: float, humidity: float, wind_speed: float, wind_bearing: float) -> None:
		self.condition = condition
		self.temperature = temperature
		self.pressure = pressure
		self.humidity = humidity
		self.wind_speed = wind_speed
		self.wind_bearing = wind_bearing


class AladinWeatherForecast:

	def __init__(self, datetime: datetime, condition: str, temperature: float, precipitation: float, pressure: float, wind_speed: float, wind_bearing: float) -> None:
		self.datetime = datetime
		self.condition = condition
		self.temperature = temperature
		self.precipitation = precipitation
		self.pressure = pressure
		self.wind_speed = wind_speed
		self.wind_bearing = wind_bearing


class AladinWeather:

	def __init__(self, actual_weather: AladinActualWeather) -> None:
		self.actual_weather: AladinActualWeather = actual_weather
		self.hourly_forecasts: List[AladinWeatherForecast] = []

	def add_hourly_forecast(self, forecast: AladinWeatherForecast) -> None:
		self.hourly_forecasts.append(forecast)


class AladinOnlineCoordinator(DataUpdateCoordinator):

	def __init__(self, hass: core.HomeAssistant, config: MappingProxyType) -> None:
		super().__init__(hass, LOGGER, name=DOMAIN, update_interval=timedelta(hours=1), update_method=self.update)

		self._config: MappingProxyType = config

	async def update(self) -> AladinWeather:
		session = aiohttp_client.async_get_clientsession(self.hass)
		response = await session.get(URL.format(self._config[CONF_LATITUDE], self._config[CONF_LONGITUDE]))

		if response.status != HTTP_OK:
			raise ServiceUnavailable

		# The URL returns "text/html" so ignore content_type check
		data = await response.json(content_type = None)

		data_time = AladinOnlineCoordinator._format_datetime(data[DATA_TIME])
		now = datetime.now()

		actual_index = int(math.floor((now.timestamp() - data_time.timestamp()) / 3600))
		condition_actual_index = int(math.floor(actual_index / 2))

		parameters = data[DATA_PARAMETERS]

		actual_weather = AladinActualWeather(
			AladinOnlineCoordinator._format_condition(data[DATA_CONDITIONS][condition_actual_index]),
			AladinOnlineCoordinator._format_temperature(parameters[DATA_PARAMETER_TEMPERATURE][actual_index]),
			AladinOnlineCoordinator._format_pressure(parameters[DATA_PARAMETER_PRESSURE][actual_index]),
			AladinOnlineCoordinator._format_humidity(parameters[DATA_PARAMETER_HUMIDITY][actual_index]),
			AladinOnlineCoordinator._format_wind_speed(parameters[DATA_PARAMETER_WIND_SPEED][actual_index]),
			AladinOnlineCoordinator._format_wind_direction(parameters[DATA_PARAMETER_WIND_DIRECTION][actual_index]),
		)

		weather = AladinWeather(actual_weather)

		for i in range(actual_index + 1, data[DATA_FORECAST_LENGTH]):
			forecast_datetime = data_time + timedelta(hours=i)
			forecast_condition_index = int(math.floor(i / 2))

			forecast = AladinWeatherForecast(
				forecast_datetime,
				AladinOnlineCoordinator._format_condition(data[DATA_CONDITIONS][forecast_condition_index]),
				AladinOnlineCoordinator._format_temperature(parameters[DATA_PARAMETER_TEMPERATURE][i]),
				AladinOnlineCoordinator._format_precipitation(parameters[DATA_PARAMETER_PRECIPITATION][i]),
				AladinOnlineCoordinator._format_pressure(parameters[DATA_PARAMETER_PRESSURE][i]),
				AladinOnlineCoordinator._format_wind_speed(parameters[DATA_PARAMETER_WIND_SPEED][i]),
				AladinOnlineCoordinator._format_wind_direction(parameters[DATA_PARAMETER_WIND_DIRECTION][i]),
			)

			weather.add_hourly_forecast(forecast)

		return weather

	@staticmethod
	def _format_datetime(raw: str) -> datetime:
		dt.set_default_time_zone(pytz.timezone("Europe/Prague"))
		return dt.parse_datetime(raw)

	@staticmethod
	def _format_condition(raw: str) -> str:
		mapping = {
			"wi_cloud_rain_light": ATTR_CONDITION_POURING,
			"wi_cloud": ATTR_CONDITION_CLOUDY,
			"wi_night_cloud": ATTR_CONDITION_PARTLYCLOUDY,
			"wi_day_cloud": ATTR_CONDITION_PARTLYCLOUDY,
			"wi_night": ATTR_CONDITION_CLEAR_NIGHT,
			"wi_day": ATTR_CONDITION_SUNNY,
		}

		if raw in mapping:
			return mapping[raw]

		# Temporary
		LOGGER.debug("Unknown condition: {}".format(raw))
		return ATTR_CONDITION_SUNNY

	@staticmethod
	def _format_temperature(raw: float) -> float:
		return round(raw, 1)

	@staticmethod
	def _format_precipitation(raw: float) -> float:
		return round(raw, 1)

	@staticmethod
	def _format_pressure(raw: float) -> float:
		return round(raw / 100, 1)

	@staticmethod
	def _format_humidity(raw: float) -> float:
		return round(raw * 100)

	@staticmethod
	def _format_wind_speed(raw: float) -> float:
		return round(raw * 3.6, 1)

	@staticmethod
	def _format_wind_direction(raw: float) -> float:
		return round(raw / 100, 2)
