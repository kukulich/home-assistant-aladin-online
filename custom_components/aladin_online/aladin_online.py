from datetime import datetime, timedelta
from homeassistant import core
from homeassistant.components.weather import (
	ATTR_CONDITION_CLEAR_NIGHT,
	ATTR_CONDITION_CLOUDY,
	ATTR_CONDITION_PARTLYCLOUDY,
	ATTR_CONDITION_POURING,
	ATTR_CONDITION_SNOWY,
	ATTR_CONDITION_SUNNY,
	ATTR_CONDITION_RAINY,
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
from .errors import NoData, ServiceUnavailable
from types import MappingProxyType
from typing import Final, List

DATA_TIME: Final = "forecastTimeIso"
DATA_FORECAST_LENGTH: Final = "forecastLength"
DATA_PARAMETERS: Final = "parameterValues"
DATA_CONDITIONS: Final = "weatherIconNames"
DATA_PARAMETER_CLOUDS: Final = "CLOUDS_TOTAL"
DATA_PARAMETER_HUMIDITY: Final = "HUMIDITY"
DATA_PARAMETER_PRECIPITATION: Final = "PRECIPITATION_TOTAL"
DATA_PARAMETER_PRESSURE: Final = "PRESSURE"
DATA_PARAMETER_SNOW_PRECIPITATION: Final = "PRECIPITATION_SNOW"
DATA_PARAMETER_TEMPERATURE: Final = "TEMPERATURE"
DATA_PARAMETER_APPARENT_TEMPERATURE: Final = "APPARENT_TEMPERATURE"
DATA_PARAMETER_WIND_DIRECTION: Final = "WIND_DIRECTION"
DATA_PARAMETER_WIND_SPEED: Final = "WIND_SPEED"
DATA_PARAMETER_WIND_GUST_SPEED: Final = "WIND_GUST_SPEED"
DATA_PARAMETER_WIND_GUST_DIRECTION: Final = "WIND_GUST_DIRECTION"


class AladinActualWeather:

	def __init__(
		self,
		condition: str,
		temperature: float,
		apparent_temperature: float,
		precipitation: float,
		pressure: float,
		humidity: float,
		clouds: float,
		wind_speed: float,
		wind_bearing: float,
		wind_gust_speed: float,
		wind_gust_bearing: float,
		snow_precipitation: float,
	) -> None:
		self.condition = condition
		self.temperature = temperature
		self.apparent_temperature = apparent_temperature
		self.precipitation = precipitation
		self.pressure = pressure
		self.humidity = humidity
		self.clouds = clouds
		self.wind_speed = wind_speed
		self.wind_bearing = wind_bearing
		self.wind_gust_speed = wind_gust_speed
		self.wind_gust_bearing = wind_gust_bearing
		self.snow_precipitation = snow_precipitation

	@property
	def wind_speed_in_kilometers_per_hour(self) -> float:
		return round(self.wind_speed * 3.6, 1)

	@property
	def wind_gust_speed_in_kilometers_per_hour(self) -> float:
		return round(self.wind_gust_speed * 3.6, 1)


class AladinWeatherForecast:

	def __init__(self, forecast_datetime: datetime, condition: str, temperature: float, precipitation: float, pressure: float, wind_speed: float, wind_bearing: float) -> None:
		self.datetime = forecast_datetime
		self.condition = condition
		self.temperature = temperature
		self.precipitation = precipitation
		self.pressure = pressure
		self.wind_speed = wind_speed
		self.wind_bearing = wind_bearing
		self.wind_speed_in_kilometers_per_hour = round(wind_speed * 3.6, 1)


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

		self._data = None

	async def update(self) -> AladinWeather:
		if self._should_update_data():
			try:
				await self._update_data()
			except Exception as ex:
				if self._data is None:
					raise ex

		if self._data is None:
			raise ServiceUnavailable

		data_time = AladinOnlineCoordinator._format_datetime(self._data[DATA_TIME])
		now = datetime.now()

		actual_index = int(math.floor((now.timestamp() - data_time.timestamp()) / 3600))
		condition_actual_index = int(math.floor(actual_index / 2))

		parameters = self._data[DATA_PARAMETERS]

		if condition_actual_index >= len(self._data[DATA_CONDITIONS]):
			raise NoData

		actual_weather = AladinActualWeather(
			AladinOnlineCoordinator._format_condition(self._data[DATA_CONDITIONS][condition_actual_index]),
			AladinOnlineCoordinator._format_temperature(parameters[DATA_PARAMETER_TEMPERATURE][actual_index]),
			AladinOnlineCoordinator._format_temperature(parameters[DATA_PARAMETER_APPARENT_TEMPERATURE][actual_index]),
			AladinOnlineCoordinator._format_precipitation(parameters[DATA_PARAMETER_PRECIPITATION][actual_index]),
			AladinOnlineCoordinator._format_pressure(parameters[DATA_PARAMETER_PRESSURE][actual_index]),
			AladinOnlineCoordinator._format_percent(parameters[DATA_PARAMETER_HUMIDITY][actual_index]),
			AladinOnlineCoordinator._format_percent(parameters[DATA_PARAMETER_CLOUDS][actual_index]),
			AladinOnlineCoordinator._format_wind_speed(parameters[DATA_PARAMETER_WIND_SPEED][actual_index]),
			AladinOnlineCoordinator._format_wind_direction(parameters[DATA_PARAMETER_WIND_DIRECTION][actual_index]),
			AladinOnlineCoordinator._format_wind_speed(parameters[DATA_PARAMETER_WIND_GUST_SPEED][actual_index]),
			AladinOnlineCoordinator._format_wind_direction(parameters[DATA_PARAMETER_WIND_GUST_DIRECTION][actual_index]),
			AladinOnlineCoordinator._format_precipitation(parameters[DATA_PARAMETER_SNOW_PRECIPITATION][actual_index]),
		)

		weather = AladinWeather(actual_weather)

		for i in range(actual_index + 1, self._data[DATA_FORECAST_LENGTH]):
			forecast_datetime = data_time + timedelta(hours=i)
			forecast_condition_index = int(math.floor(i / 2))

			forecast = AladinWeatherForecast(
				forecast_datetime,
				AladinOnlineCoordinator._format_condition(self._data[DATA_CONDITIONS][forecast_condition_index]),
				AladinOnlineCoordinator._format_temperature(parameters[DATA_PARAMETER_TEMPERATURE][i]),
				AladinOnlineCoordinator._format_precipitation(parameters[DATA_PARAMETER_PRECIPITATION][i]),
				AladinOnlineCoordinator._format_pressure(parameters[DATA_PARAMETER_PRESSURE][i]),
				AladinOnlineCoordinator._format_wind_speed(parameters[DATA_PARAMETER_WIND_SPEED][i]),
				AladinOnlineCoordinator._format_wind_direction(parameters[DATA_PARAMETER_WIND_DIRECTION][i]),
			)

			weather.add_hourly_forecast(forecast)

		return weather

	def _should_update_data(self) -> bool:
		if self._data is None:
			return True

		# Updates are in 0, 5, 12 and 17 hour so wait an hour to be sure the update is there
		if datetime.now().hour in [1, 6, 13, 18]:
			return True

		return False

	async def _update_data(self) -> None:
		session = aiohttp_client.async_get_clientsession(self.hass)
		response = await session.get(URL.format(self._config[CONF_LATITUDE], self._config[CONF_LONGITUDE]))

		if response.status != HTTP_OK:
			raise ServiceUnavailable

		# The URL returns "text/html" so ignore content_type check
		self._data = await response.json(content_type=None)

	@staticmethod
	def _format_datetime(raw: str) -> datetime:
		dt.set_default_time_zone(pytz.timezone("Europe/Prague"))
		return dt.parse_datetime(raw)

	@staticmethod
	def _format_condition(raw: str) -> str:
		mapping = {
			"wi_cloud_snow_heavy": ATTR_CONDITION_SNOWY,
			"wi_cloud_snow_medium": ATTR_CONDITION_SNOWY,
			"wi_cloud_snow_light": ATTR_CONDITION_SNOWY,
			"wi_night_cloud_snow": ATTR_CONDITION_SNOWY,
			"wi_day_cloud_snow": ATTR_CONDITION_SNOWY,
			"wi_day_cloud_rain": ATTR_CONDITION_RAINY,
			"wi_night_cloud_rain": ATTR_CONDITION_RAINY,
			"wi_cloud_rain_heavy": ATTR_CONDITION_RAINY,
			"wi_cloud_rain_medium": ATTR_CONDITION_RAINY,
			"wi_cloud_rain_light": ATTR_CONDITION_POURING,
			"wi_cloud": ATTR_CONDITION_CLOUDY,
			"wi_night_cloud": ATTR_CONDITION_PARTLYCLOUDY,
			"wi_day_cloud": ATTR_CONDITION_PARTLYCLOUDY,
			"wi_night": ATTR_CONDITION_CLEAR_NIGHT,
			"wi_day": ATTR_CONDITION_SUNNY,
		}

		if raw in mapping:
			return mapping[raw]

		LOGGER.error("Unknown condition: {}".format(raw))
		return ATTR_CONDITION_SUNNY

	@staticmethod
	def _format_temperature(raw: float) -> float:
		return round(raw, 1)

	@staticmethod
	def _format_percent(raw: float) -> float:
		return round(raw * 100)

	@staticmethod
	def _format_precipitation(raw: float) -> float:
		return abs(round(raw, 1))

	@staticmethod
	def _format_pressure(raw: float) -> float:
		return round(raw / 100, 1)

	@staticmethod
	def _format_wind_speed(raw: float) -> float:
		return round(raw, 1)

	@staticmethod
	def _format_wind_direction(raw: float) -> float:
		return round(raw / 100, 2)
