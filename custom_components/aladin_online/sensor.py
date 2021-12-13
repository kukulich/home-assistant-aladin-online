from __future__ import annotations
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
	SensorDeviceClass,
	SensorEntity,
	SensorStateClass,
)
from homeassistant.const import (
	CONF_NAME,
)
from homeassistant.core import callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator
from types import MappingProxyType
from typing import Final
from .aladin_online import AladinActualWeather
from .const import (
	DOMAIN,
	DATA_COORDINATOR,
	NAME,
)

SENSOR_APPARENT_TEMPERATURE: Final = "apparent_temperature"
SENSOR_CLOUDS: Final = "clouds"
SENSOR_HUMIDITY: Final = "humidity"
SENSOR_PRECIPITATION: Final = "precipitation"
SENSOR_PRESSURE: Final = "pressure"
SENSOR_SNOW_PRECIPITATION: Final = "snow_precipitation"
SENSOR_TEMPERATURE: Final = "temperature"
SENSOR_WIND_SPEED: Final = "wind_speed"
SENSOR_WIND_SPEED_IN_KILOMETERS_PER_HOUR: Final = "wind_speed_in_km_h"
SENSOR_WIND_GUST_SPEED: Final = "wind_gust_speed"
SENSOR_WIND_GUST_SPEED_IN_KILOMETERS_PER_HOUR: Final = "wind_gust_speed_in_km_h"

SENSORS: Final = (
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
)

SENSOR_NAMES: Final = {
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

SENSOR_DEVICE_CLASSES: Final = {
	SENSOR_APPARENT_TEMPERATURE: SensorDeviceClass.TEMPERATURE,
	SENSOR_HUMIDITY: SensorDeviceClass.HUMIDITY,
	SENSOR_PRESSURE: SensorDeviceClass.PRESSURE,
	SENSOR_TEMPERATURE: SensorDeviceClass.TEMPERATURE,
}

SENSOR_UNIT_OF_MEASUREMENTS: Final = {
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

SENSOR_ICONS: Final = {
	SENSOR_CLOUDS: "mdi:weather-partly-cloudy",
	SENSOR_PRECIPITATION: "mdi:cup-water",
	SENSOR_SNOW_PRECIPITATION: "mdi:weather-snowy",
	SENSOR_WIND_SPEED: "mdi:weather-windy",
	SENSOR_WIND_SPEED_IN_KILOMETERS_PER_HOUR: "mdi:weather-windy",
	SENSOR_WIND_GUST_SPEED: "mdi:weather-windy",
	SENSOR_WIND_GUST_SPEED_IN_KILOMETERS_PER_HOUR: "mdi:weather-windy",
}

DEVICE_INFO: Final[DeviceInfo] = {
	"identifiers": {(DOMAIN,)},
	"model": "Weather forecast",
	"default_name": "Weather forecast",
	"manufacturer": NAME,
	"entry_type": "service",
}

async def async_setup_entry(hass: core.HomeAssistant, config_entry: config_entries.ConfigEntry, async_add_entities) -> None:
	coordinator = hass.data[DOMAIN][config_entry.entry_id][DATA_COORDINATOR]

	for sensor_type in SENSORS:
		async_add_entities([
			SensorEntity(coordinator, config_entry.data, sensor_type),
		])


class SensorEntity(CoordinatorEntity, SensorEntity):

	def __init__(self, coordinator: DataUpdateCoordinator, config: MappingProxyType, sensor_type: str):
		super().__init__(coordinator)

		self._sensor_type: str = sensor_type

		self._attr_unique_id = "{}.{}".format(
			config[CONF_NAME],
			self._sensor_type,
		)

		self._attr_name = "{}: {}".format(
			config[CONF_NAME],
			SENSOR_NAMES[self._sensor_type],
		)
		self._attr_icon = SENSOR_ICONS[self._sensor_type] if self._sensor_type in SENSOR_ICONS else None
		self._attr_native_unit_of_measurement = SENSOR_UNIT_OF_MEASUREMENTS[self._sensor_type] if self._sensor_type in SENSOR_UNIT_OF_MEASUREMENTS else None
		self._attr_state_class = SensorStateClass.MEASUREMENT

		self._attr_device_class = SENSOR_DEVICE_CLASSES[self._sensor_type] if self._sensor_type in SENSOR_DEVICE_CLASSES else None
		self._attr_device_info = DEVICE_INFO

		self._update_attributes()

	def _update_attributes(self):
		actual_weather: AladinActualWeather = self.coordinator.data.actual_weather

		if self._sensor_type == SENSOR_APPARENT_TEMPERATURE:
			self._attr_native_value = actual_weather.apparent_temperature
		elif self._sensor_type == SENSOR_CLOUDS:
			self._attr_native_value = actual_weather.clouds
		elif self._sensor_type == SENSOR_HUMIDITY:
			self._attr_native_value = actual_weather.humidity
		elif self._sensor_type == SENSOR_PRECIPITATION:
			self._attr_native_value = actual_weather.precipitation
		elif self._sensor_type == SENSOR_PRESSURE:
			self._attr_native_value = actual_weather.pressure
		elif self._sensor_type == SENSOR_SNOW_PRECIPITATION:
			self._attr_native_value = actual_weather.snow_precipitation
		elif self._sensor_type == SENSOR_TEMPERATURE:
			self._attr_native_value = actual_weather.temperature
		elif self._sensor_type == SENSOR_WIND_SPEED:
			self._attr_native_value = actual_weather.wind_speed
		elif self._sensor_type == SENSOR_WIND_SPEED_IN_KILOMETERS_PER_HOUR:
			self._attr_native_value = actual_weather.wind_speed_in_kilometers_per_hour
		elif self._sensor_type == SENSOR_WIND_GUST_SPEED:
			self._attr_native_value = actual_weather.wind_gust_speed
		elif self._sensor_type == SENSOR_WIND_GUST_SPEED_IN_KILOMETERS_PER_HOUR:
			self._attr_native_value = actual_weather.wind_gust_speed_in_kilometers_per_hour

	@callback
	def _handle_coordinator_update(self) -> None:
		self._update_attributes()
		super()._handle_coordinator_update()
