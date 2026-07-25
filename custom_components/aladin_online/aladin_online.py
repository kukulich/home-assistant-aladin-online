from collections.abc import Mapping
from datetime import datetime, timedelta
from http import HTTPStatus
import math
from typing import Any, NotRequired, TypedDict, cast

from homeassistant import core
from homeassistant.components.weather import (
	ATTR_CONDITION_CLEAR_NIGHT,
	ATTR_CONDITION_CLOUDY,
	ATTR_CONDITION_FOG,
	ATTR_CONDITION_HAIL,
	ATTR_CONDITION_LIGHTNING_RAINY,
	ATTR_CONDITION_PARTLYCLOUDY,
	ATTR_CONDITION_SNOWY,
	ATTR_CONDITION_SNOWY_RAINY,
	ATTR_CONDITION_SUNNY,
	ATTR_CONDITION_RAINY,
)
from homeassistant.const import (
	CONF_LATITUDE,
	CONF_LONGITUDE,
)
from homeassistant.helpers import aiohttp_client
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt

from .const import (
	DOMAIN,
	LOGGER,
	URL,
)
from .errors import NoData, ServiceUnavailable


class AladinEntry(TypedDict):
	validityTime: str
	t2m: float
	rh2m: float
	mslp: float
	cloudsTot: float
	windSpeed: float
	icon: NotRequired[int]
	prec: NotRequired[float]
	windDirection: NotRequired[float]
	windGustSpeed: NotRequired[float]
	snow: NotRequired[float]


class AladinResponse(TypedDict):
	data: list[AladinEntry]

# Mapping of CHMI numeric weather icons to Home Assistant conditions
# Icon source: https://www.chmi.cz/predpoved-pocasi/ikony-pocasi
ICON_CONDITION_MAP = {
	# Daytime icons
	10:  ATTR_CONDITION_SUNNY,           # Clear
	20:  ATTR_CONDITION_SUNNY,           # Mostly clear
	40:  ATTR_CONDITION_PARTLYCLOUDY,    # Partly cloudy
	41:  ATTR_CONDITION_RAINY,           # Partly cloudy, shower
	43:  ATTR_CONDITION_SNOWY_RAINY,     # Partly cloudy, sleet shower
	45:  ATTR_CONDITION_SNOWY,           # Partly cloudy, snow shower
	46:  ATTR_CONDITION_LIGHTNING_RAINY, # Partly cloudy, thunderstorm
	60:  ATTR_CONDITION_PARTLYCLOUDY,    # Cloudy
	61:  ATTR_CONDITION_RAINY,           # Cloudy, shower
	62:  ATTR_CONDITION_SNOWY_RAINY,     # Cloudy, freezing rain
	63:  ATTR_CONDITION_SNOWY_RAINY,     # Cloudy, sleet shower
	64:  ATTR_CONDITION_SNOWY,           # Cloudy, snowfall
	65:  ATTR_CONDITION_SNOWY,           # Cloudy, snow shower
	66:  ATTR_CONDITION_LIGHTNING_RAINY, # Cloudy, thunderstorm
	69:  ATTR_CONDITION_HAIL,            # Cloudy, hail
	70:  ATTR_CONDITION_CLOUDY,          # Mostly overcast
	71:  ATTR_CONDITION_RAINY,           # Mostly overcast, rain or shower
	72:  ATTR_CONDITION_SNOWY_RAINY,     # Mostly overcast, freezing rain
	73:  ATTR_CONDITION_SNOWY_RAINY,     # Mostly overcast, sleet
	74:  ATTR_CONDITION_SNOWY,           # Mostly overcast, snowfall
	75:  ATTR_CONDITION_SNOWY,           # Mostly overcast, snow shower
	76:  ATTR_CONDITION_LIGHTNING_RAINY, # Mostly overcast, thunderstorm
	79:  ATTR_CONDITION_HAIL,            # Mostly overcast, hail
	80:  ATTR_CONDITION_CLOUDY,          # Overcast
	81:  ATTR_CONDITION_RAINY,           # Overcast, rain or shower
	82:  ATTR_CONDITION_SNOWY_RAINY,     # Overcast, freezing rain
	83:  ATTR_CONDITION_SNOWY_RAINY,     # Overcast, sleet
	84:  ATTR_CONDITION_SNOWY,           # Overcast, snowfall
	85:  ATTR_CONDITION_SNOWY,           # Overcast, snow shower
	86:  ATTR_CONDITION_LIGHTNING_RAINY, # Overcast, thunderstorm
	89:  ATTR_CONDITION_HAIL,            # Overcast, hail
	90:  ATTR_CONDITION_FOG,             # Fog
	91:  ATTR_CONDITION_FOG,             # Fog, shower
	92:  ATTR_CONDITION_FOG,             # Fog, freezing rain
	93:  ATTR_CONDITION_FOG,             # Fog, sleet
	94:  ATTR_CONDITION_FOG,             # Fog, snowfall
	# Nighttime icons
	110: ATTR_CONDITION_CLEAR_NIGHT,     # Clear
	120: ATTR_CONDITION_CLEAR_NIGHT,     # Mostly clear
	140: ATTR_CONDITION_PARTLYCLOUDY,    # Partly cloudy
	141: ATTR_CONDITION_RAINY,           # Partly cloudy, shower
	143: ATTR_CONDITION_SNOWY_RAINY,     # Partly cloudy, sleet shower
	145: ATTR_CONDITION_SNOWY,           # Partly cloudy, snow shower
	146: ATTR_CONDITION_LIGHTNING_RAINY, # Partly cloudy, thunderstorm
	160: ATTR_CONDITION_PARTLYCLOUDY,    # Cloudy
	161: ATTR_CONDITION_RAINY,           # Cloudy, shower
	162: ATTR_CONDITION_SNOWY_RAINY,     # Cloudy, freezing rain
	163: ATTR_CONDITION_SNOWY_RAINY,     # Cloudy, sleet shower
	164: ATTR_CONDITION_SNOWY,           # Cloudy, snowfall
	165: ATTR_CONDITION_SNOWY,           # Cloudy, snow shower
	166: ATTR_CONDITION_LIGHTNING_RAINY, # Cloudy, thunderstorm
	169: ATTR_CONDITION_HAIL,            # Cloudy, hail
	170: ATTR_CONDITION_CLOUDY,          # Mostly overcast
	171: ATTR_CONDITION_RAINY,           # Mostly overcast, rain or shower
	172: ATTR_CONDITION_SNOWY_RAINY,     # Mostly overcast, freezing rain
	173: ATTR_CONDITION_SNOWY_RAINY,     # Mostly overcast, sleet
	174: ATTR_CONDITION_SNOWY,           # Mostly overcast, snowfall
	175: ATTR_CONDITION_SNOWY,           # Mostly overcast, snow shower
	176: ATTR_CONDITION_LIGHTNING_RAINY, # Mostly overcast, thunderstorm
	179: ATTR_CONDITION_HAIL,            # Mostly overcast, hail
}


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


class AladinWeatherForecast:

	def __init__(
		self,
		forecast_datetime: datetime,
		condition: str,
		temperature: float,
		apparent_temperature: float,
		precipitation: float,
		pressure: float,
		wind_speed: float,
		wind_bearing: float,
		wind_gust_speed: float,
		humidity: float,
		clouds: float,
	) -> None:
		self.datetime = forecast_datetime
		self.condition = condition
		self.temperature = temperature
		self.apparent_temperature = apparent_temperature
		self.precipitation = precipitation
		self.pressure = pressure
		self.wind_speed = wind_speed
		self.wind_bearing = wind_bearing
		self.wind_gust_speed = wind_gust_speed
		self.humidity = humidity
		self.clouds = clouds


class AladinWeather:

	def __init__(self, actual_weather: AladinActualWeather) -> None:
		self.actual_weather: AladinActualWeather = actual_weather
		self.hourly_forecasts: list[AladinWeatherForecast] = []

	def add_hourly_forecast(self, forecast: AladinWeatherForecast) -> None:
		self.hourly_forecasts.append(forecast)


class AladinOnlineCoordinator(DataUpdateCoordinator[AladinWeather]):

	def __init__(self, hass: core.HomeAssistant, config: Mapping[str, Any]) -> None:
		super().__init__(hass, LOGGER, name=DOMAIN, update_interval=timedelta(minutes=30), update_method=self.update)

		self._config = config
		self._data: AladinResponse | None = None

	async def update(self) -> AladinWeather:
		if self._should_update_data():
			try:
				await self._update_data()
			except Exception as ex:
				if self._data is None:
					raise ex

		if self._data is None:
			raise ServiceUnavailable

		entries = self._data.get("data", [])
		if not entries:
			raise NoData

		now = dt.utcnow()

		# Find the current hour in the data
		actual_entry = None
		actual_index = 0
		for i, entry in enumerate(entries):
			entry_time = dt.parse_datetime(entry["validityTime"])
			if entry_time is None:
				raise NoData
			if entry_time <= now:
				actual_entry = entry
				actual_index = i
			else:
				break

		if actual_entry is None:
			actual_entry = entries[0]
			actual_index = 0

		actual_weather = AladinActualWeather(
			condition=AladinOnlineCoordinator._format_condition(actual_entry.get("icon", 0)),
			temperature=actual_entry["t2m"],
			apparent_temperature=AladinOnlineCoordinator._compute_apparent_temperature(
				actual_entry["t2m"],
				actual_entry["rh2m"],
				actual_entry["windSpeed"],
			),
			precipitation=actual_entry.get("prec", 0),
			pressure=actual_entry["mslp"],
			humidity=actual_entry["rh2m"],
			clouds=actual_entry["cloudsTot"],
			wind_speed=actual_entry["windSpeed"],
			wind_bearing=AladinOnlineCoordinator._format_wind_direction(actual_entry.get("windDirection", 0)),
			wind_gust_speed=actual_entry.get("windGustSpeed", 0),
			wind_gust_bearing=AladinOnlineCoordinator._format_wind_direction(actual_entry.get("windDirection", 0)),
			snow_precipitation=actual_entry.get("snow", 0),
		)

		weather = AladinWeather(actual_weather)

		for entry in entries[actual_index + 1:]:
			forecast_datetime = dt.parse_datetime(entry["validityTime"])
			if forecast_datetime is None:
				raise NoData

			forecast = AladinWeatherForecast(
				forecast_datetime=forecast_datetime,
				condition=AladinOnlineCoordinator._format_condition(entry.get("icon", 0)),
				temperature=entry["t2m"],
				apparent_temperature=AladinOnlineCoordinator._compute_apparent_temperature(
					entry["t2m"],
					entry["rh2m"],
					entry["windSpeed"],
				),
				precipitation=entry.get("prec", 0),
				pressure=entry["mslp"],
				wind_speed=entry["windSpeed"],
				wind_bearing=AladinOnlineCoordinator._format_wind_direction(entry.get("windDirection", 0)),
				wind_gust_speed=entry.get("windGustSpeed", 0),
				humidity=entry["rh2m"],
				clouds=entry["cloudsTot"],
			)
			weather.add_hourly_forecast(forecast)

		return weather

	def _should_update_data(self) -> bool:
		return True

	async def _update_data(self) -> None:
		session = aiohttp_client.async_get_clientsession(self.hass)
		latitude = self._config.get(CONF_LATITUDE, self.hass.config.latitude)
		longitude = self._config.get(CONF_LONGITUDE, self.hass.config.longitude)
		response = await session.get(URL.format(longitude, latitude))

		if response.status != HTTPStatus.OK:
			raise ServiceUnavailable

		self._data = cast(
			AladinResponse,
			await response.json(content_type=None),
		)

	@staticmethod
	def _format_condition(icon: int) -> str:
		if icon in ICON_CONDITION_MAP:
			return ICON_CONDITION_MAP[icon]
		LOGGER.warning("Unknown weather icon: {}".format(icon))
		return ATTR_CONDITION_SUNNY

	@staticmethod
	def _format_wind_direction(raw: float) -> float:
		return raw % 360

	@staticmethod
	def _compute_apparent_temperature(temperature: float, humidity: float, wind_speed: float) -> float:
		# Australian apparent temperature formula (Steadman / Bureau of Meteorology).
		# The data source does not provide apparent temperature, so we derive it
		# from temperature (°C), relative humidity (%) and wind speed (m/s).
		# AT = T + 0.33·e − 0.70·ws − 4.00
		# e  = (rh / 100) · 6.105 · exp(17.27·T / (237.7 + T))   (water vapour pressure in hPa)

		vapour_pressure = (humidity / 100) * 6.105 * math.exp(17.27 * temperature / (237.7 + temperature))

		return temperature + 0.33 * vapour_pressure - 0.70 * wind_speed - 4.00
