from __future__ import annotations
from homeassistant import config_entries, core
from homeassistant.const import (
	PERCENTAGE,
	PRECIPITATION_MILLIMETERS_PER_HOUR,
	PRESSURE_HPA,
	SPEED_METERS_PER_SECOND,
	TEMP_CELSIUS,
)
from homeassistant.components.sensor import (
	SensorDeviceClass,
	SensorEntity as ComponentSensorEntity,
	SensorEntityDescription,
	SensorStateClass,
)
from homeassistant.const import (
	CONF_NAME,
)
from homeassistant.core import callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator
from homeassistant.helpers.device_registry import DeviceEntryType
from types import MappingProxyType
from typing import Dict, Final
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
SENSOR_WIND_GUST_SPEED: Final = "wind_gust_speed"

SENSORS: Dict[str, SensorEntityDescription] = {
	SENSOR_APPARENT_TEMPERATURE: SensorEntityDescription(
		key=SENSOR_APPARENT_TEMPERATURE,
		name="Apparent temperature",
		device_class=SensorDeviceClass.TEMPERATURE,
		native_unit_of_measurement=TEMP_CELSIUS,
		state_class=SensorStateClass.MEASUREMENT,
	),
	SENSOR_CLOUDS: SensorEntityDescription(
		key=SENSOR_CLOUDS,
		name="Clouds",
		icon="mdi:weather-partly-cloudy",
		native_unit_of_measurement=PERCENTAGE,
		state_class=SensorStateClass.MEASUREMENT,
	),
	SENSOR_HUMIDITY: SensorEntityDescription(
		key=SENSOR_HUMIDITY,
		name="Humidity",
		device_class=SensorDeviceClass.HUMIDITY,
		native_unit_of_measurement=PERCENTAGE,
		state_class=SensorStateClass.MEASUREMENT,
	),
	SENSOR_PRECIPITATION: SensorEntityDescription(
		key=SENSOR_PRECIPITATION,
		name="Precipitation",
		icon="mdi:cup-water",
		native_unit_of_measurement=PRECIPITATION_MILLIMETERS_PER_HOUR,
		state_class=SensorStateClass.MEASUREMENT,
	),
	SENSOR_PRESSURE: SensorEntityDescription(
		key=SENSOR_PRESSURE,
		name="Pressure",
		device_class=SensorDeviceClass.PRESSURE,
		native_unit_of_measurement=PRESSURE_HPA,
		state_class=SensorStateClass.MEASUREMENT,
	),
	SENSOR_SNOW_PRECIPITATION: SensorEntityDescription(
		key=SENSOR_SNOW_PRECIPITATION,
		name="Snow precipitation",
		icon="mdi:weather-snowy",
		native_unit_of_measurement=PERCENTAGE,
		state_class=SensorStateClass.MEASUREMENT,
	),
	SENSOR_TEMPERATURE: SensorEntityDescription(
		key=SENSOR_TEMPERATURE,
		name="Temperature",
		device_class=SensorDeviceClass.TEMPERATURE,
		native_unit_of_measurement=TEMP_CELSIUS,
		state_class=SensorStateClass.MEASUREMENT,
	),
	SENSOR_WIND_SPEED: SensorEntityDescription(
		key=SENSOR_WIND_SPEED,
		name="Wind speed",
		icon="mdi:weather-windy",
		native_unit_of_measurement=SPEED_METERS_PER_SECOND,
		state_class=SensorStateClass.MEASUREMENT,
	),
	SENSOR_WIND_GUST_SPEED: SensorEntityDescription(
		key=SENSOR_WIND_GUST_SPEED,
		name="Wind gust speed",
		icon="mdi:weather-windy",
		native_unit_of_measurement=SPEED_METERS_PER_SECOND,
		state_class=SensorStateClass.MEASUREMENT,
	),
}

async def async_setup_entry(hass: core.HomeAssistant, config_entry: config_entries.ConfigEntry, async_add_entities) -> None:
	coordinator = hass.data[DOMAIN][config_entry.entry_id][DATA_COORDINATOR]

	for sensor_type in SENSORS:
		async_add_entities([
			SensorEntity(coordinator, config_entry.data, sensor_type, SENSORS[sensor_type]),
		])


class SensorEntity(CoordinatorEntity, ComponentSensorEntity):

	_attr_has_entity_name = True

	def __init__(self, coordinator: DataUpdateCoordinator, config: MappingProxyType, sensor_type: str, entity_description: SensorEntityDescription):
		super().__init__(coordinator)

		self._sensor_type: str = sensor_type
		self.entity_description = entity_description

		self._attr_unique_id = "{}.{}".format(
			config[CONF_NAME],
			self._sensor_type,
		)

		self._attr_device_info = DeviceInfo(
			identifiers={(DOMAIN,)},
			model="Weather forecast",
			name=config[CONF_NAME],
			manufacturer=NAME,
			entry_type=DeviceEntryType.SERVICE,
		)

		self._update_attributes()

	def _update_attributes(self):
		if self.coordinator.data is None:
			return

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
		elif self._sensor_type == SENSOR_WIND_GUST_SPEED:
			self._attr_native_value = actual_weather.wind_gust_speed

	@callback
	def _handle_coordinator_update(self) -> None:
		self._update_attributes()
		super()._handle_coordinator_update()
