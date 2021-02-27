from homeassistant import config_entries, core
from homeassistant.const import (
	PERCENTAGE,
	PRESSURE_HPA,
	SPEED_KILOMETERS_PER_HOUR,
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

SENSOR_HUMIDITY = "humidity"
SENSOR_PRESSURE = "pressure"
SENSOR_TEMPERATURE = "temperature"
SENSOR_WIND_SPEED = "wind_speed"

SENSOR_NAMES = {
	SENSOR_HUMIDITY: "Humidity",
	SENSOR_PRESSURE: "Pressure",
	SENSOR_TEMPERATURE: "Temperature",
	SENSOR_WIND_SPEED: "Wind speed",
}

SENSOR_DEVICE_CLASSES = {
	SENSOR_HUMIDITY: DEVICE_CLASS_HUMIDITY,
	SENSOR_PRESSURE: DEVICE_CLASS_PRESSURE,
	SENSOR_TEMPERATURE: DEVICE_CLASS_TEMPERATURE,
}

SENSOR_UNIT_OF_MEASUREMENTS = {
	SENSOR_HUMIDITY: PERCENTAGE,
	SENSOR_PRESSURE: PRESSURE_HPA,
	SENSOR_TEMPERATURE: TEMP_CELSIUS,
	SENSOR_WIND_SPEED: SPEED_KILOMETERS_PER_HOUR,
}

SENSOR_ICONS = {
	SENSOR_WIND_SPEED: "mdi:weather-windy",
}


async def async_setup_entry(hass: core.HomeAssistant, config_entry: config_entries.ConfigEntry, async_add_entities) -> None:
	coordinator = hass.data[DOMAIN][config_entry.entry_id][DATA_COORDINATOR]

	for sensor_type in [SENSOR_HUMIDITY, SENSOR_PRESSURE, SENSOR_TEMPERATURE, SENSOR_WIND_SPEED]:
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

		states = {
			SENSOR_HUMIDITY: actual_weather.humidity,
			SENSOR_PRESSURE: actual_weather.pressure,
			SENSOR_TEMPERATURE: actual_weather.temperature,
			SENSOR_WIND_SPEED: actual_weather.wind_speed,
		}

		return states[self._sensor_type]

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
