from homeassistant import config_entries, core
from homeassistant.const import (
	PERCENTAGE,
	PRECIPITATION_MILLIMETERS_PER_HOUR,
	PRESSURE_HPA,
	SPEED_KILOMETERS_PER_HOUR,
	SPEED_METERS_PER_SECOND,
	TEMP_CELSIUS,
)
from homeassistant.components.sensor import (
	DEVICE_CLASS_HUMIDITY,
	DEVICE_CLASS_PRESSURE,
	DEVICE_CLASS_TEMPERATURE,
)
from homeassistant.const import (
	CONF_NAME,
)
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator
from types import MappingProxyType
from typing import Optional
from .aladin_online import AladinWeather
from .const import (
	DOMAIN,
	DATA_COORDINATOR,
)

SENSOR_APPARENT_TEMPERATURE = "apparent_temperature"
SENSOR_CLOUDS = "clouds"
SENSOR_HUMIDITY = "humidity"
SENSOR_PRECIPITATION = "precipitation"
SENSOR_PRESSURE = "pressure"
SENSOR_SNOW_PRECIPITATION = "snow_precipitation"
SENSOR_TEMPERATURE = "temperature"
SENSOR_WIND_SPEED = "wind_speed"
SENSOR_WIND_SPEED_IN_KILOMETERS_PER_HOUR = "wind_speed_in_km_h"
SENSOR_WIND_GUST_SPEED = "wind_gust_speed"
SENSOR_WIND_GUST_SPEED_IN_KILOMETERS_PER_HOUR = "wind_gust_speed_in_km_h"

SENSORS = [
	SENSOR_APPARENT_TEMPERATURE,
	SENSOR_CLOUDS,
	SENSOR_HUMIDITY,
	SENSOR_PRECIPITATION,
	SENSOR_PRESSURE,
	SENSOR_SNOW_PRECIPITATION,
	SENSOR_TEMPERATURE,
	SENSOR_WIND_SPEED,
	SENSOR_WIND_SPEED_IN_KILOMETERS_PER_HOUR,
	SENSOR_WIND_GUST_SPEED,
	SENSOR_WIND_GUST_SPEED_IN_KILOMETERS_PER_HOUR,
]

SENSOR_NAMES = {
	SENSOR_APPARENT_TEMPERATURE: "Apparent temperature",
	SENSOR_CLOUDS: "Clouds",
	SENSOR_HUMIDITY: "Humidity",
	SENSOR_PRECIPITATION: "Precipitation",
	SENSOR_PRESSURE: "Pressure",
	SENSOR_SNOW_PRECIPITATION: "Snow precipitation",
	SENSOR_TEMPERATURE: "Temperature",
	SENSOR_WIND_SPEED: "Wind speed",
	SENSOR_WIND_SPEED_IN_KILOMETERS_PER_HOUR: "Wind speed ({})".format(SPEED_KILOMETERS_PER_HOUR),
	SENSOR_WIND_GUST_SPEED: "Wind gust speed",
	SENSOR_WIND_GUST_SPEED_IN_KILOMETERS_PER_HOUR: "Wind gust speed ({})".format(SPEED_KILOMETERS_PER_HOUR),
}

SENSOR_DEVICE_CLASSES = {
	SENSOR_APPARENT_TEMPERATURE: DEVICE_CLASS_TEMPERATURE,
	SENSOR_HUMIDITY: DEVICE_CLASS_HUMIDITY,
	SENSOR_PRESSURE: DEVICE_CLASS_PRESSURE,
	SENSOR_TEMPERATURE: DEVICE_CLASS_TEMPERATURE,
}

SENSOR_UNIT_OF_MEASUREMENTS = {
	SENSOR_APPARENT_TEMPERATURE: TEMP_CELSIUS,
	SENSOR_CLOUDS: PERCENTAGE,
	SENSOR_HUMIDITY: PERCENTAGE,
	SENSOR_PRECIPITATION: PRECIPITATION_MILLIMETERS_PER_HOUR,
	SENSOR_PRESSURE: PRESSURE_HPA,
	SENSOR_SNOW_PRECIPITATION: PERCENTAGE,
	SENSOR_TEMPERATURE: TEMP_CELSIUS,
	SENSOR_WIND_SPEED: SPEED_METERS_PER_SECOND,
	SENSOR_WIND_SPEED_IN_KILOMETERS_PER_HOUR: SPEED_KILOMETERS_PER_HOUR,
	SENSOR_WIND_GUST_SPEED: SPEED_METERS_PER_SECOND,
	SENSOR_WIND_GUST_SPEED_IN_KILOMETERS_PER_HOUR: SPEED_KILOMETERS_PER_HOUR,
}

SENSOR_ICONS = {
	SENSOR_CLOUDS: "mdi:weather-partly-cloudy",
	SENSOR_PRECIPITATION: "mdi:cup-water",
	SENSOR_SNOW_PRECIPITATION: "mdi:weather-snowy",
	SENSOR_WIND_SPEED: "mdi:weather-windy",
	SENSOR_WIND_SPEED_IN_KILOMETERS_PER_HOUR: "mdi:weather-windy",
	SENSOR_WIND_GUST_SPEED: "mdi:weather-windy",
	SENSOR_WIND_GUST_SPEED_IN_KILOMETERS_PER_HOUR: "mdi:weather-windy",
}


async def async_setup_entry(hass: core.HomeAssistant, config_entry: config_entries.ConfigEntry, async_add_entities) -> None:
	coordinator = hass.data[DOMAIN][config_entry.entry_id][DATA_COORDINATOR]

	for sensor_type in SENSORS:
		async_add_entities([
			SensorEntity(coordinator, config_entry.data, sensor_type),
		])


class SensorEntity(CoordinatorEntity):

	def __init__(self, coordinator: DataUpdateCoordinator, config: MappingProxyType, sensor_type: str):
		super().__init__(coordinator)

		self._config: MappingProxyType = config
		self._sensor_type: str = sensor_type

	@property
	def unique_id(self) -> str:
		return "{}.{}".format(
			self._config[CONF_NAME],
			self._sensor_type,
		)

	@property
	def name(self) -> str:
		return "{}: {}".format(
			self._config[CONF_NAME],
			SENSOR_NAMES[self._sensor_type],
		)

	@property
	def state(self) -> StateType:
		actual_weather = self._weather.actual_weather

		if self._sensor_type == SENSOR_APPARENT_TEMPERATURE:
			return actual_weather.apparent_temperature
		elif self._sensor_type == SENSOR_CLOUDS:
			return actual_weather.clouds
		elif self._sensor_type == SENSOR_HUMIDITY:
			return actual_weather.humidity
		elif self._sensor_type == SENSOR_PRECIPITATION:
			return actual_weather.precipitation
		elif self._sensor_type == SENSOR_PRESSURE:
			return actual_weather.pressure
		elif self._sensor_type == SENSOR_SNOW_PRECIPITATION:
			return actual_weather.snow_precipitation
		elif self._sensor_type == SENSOR_TEMPERATURE:
			return actual_weather.temperature
		elif self._sensor_type == SENSOR_WIND_SPEED:
			return actual_weather.wind_speed
		elif self._sensor_type == SENSOR_WIND_SPEED_IN_KILOMETERS_PER_HOUR:
			return actual_weather.wind_speed_in_kilometers_per_hour
		elif self._sensor_type == SENSOR_WIND_GUST_SPEED:
			return actual_weather.wind_gust_speed
		elif self._sensor_type == SENSOR_WIND_GUST_SPEED_IN_KILOMETERS_PER_HOUR:
			return actual_weather.wind_gust_speed_in_kilometers_per_hour

		return None

	@property
	def device_class(self) -> Optional[str]:
		return SENSOR_DEVICE_CLASSES[self._sensor_type] if self._sensor_type in SENSOR_DEVICE_CLASSES else None

	@property
	def unit_of_measurement(self) -> Optional[str]:
		return SENSOR_UNIT_OF_MEASUREMENTS[self._sensor_type] if self._sensor_type in SENSOR_UNIT_OF_MEASUREMENTS else None

	@property
	def icon(self) -> Optional[str]:
		return SENSOR_ICONS[self._sensor_type] if self._sensor_type in SENSOR_ICONS else None

	@property
	def _weather(self) -> AladinWeather:
		return self.coordinator.data
