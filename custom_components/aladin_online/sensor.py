from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from homeassistant.const import (
	PERCENTAGE,
	UnitOfPressure,
	UnitOfSpeed,
	UnitOfTemperature,
	UnitOfVolumetricFlux,
)
from homeassistant.components.sensor import (
	SensorDeviceClass,
	SensorEntity as ComponentSensorEntity,
	SensorEntityDescription as ComponentSensorEntityDescription,
	SensorStateClass,
)
from homeassistant.const import (
	CONF_NAME,
)
from homeassistant.core import callback, HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator
from homeassistant.helpers.device_registry import DeviceEntryType
from types import MappingProxyType
from typing import Dict
from . import AladinOnlineConfigEntry
from .aladin_online import AladinActualWeather
from .const import (
	DOMAIN,
	NAME,
)

class SensorType(StrEnum):
	APPARENT_TEMPERATURE = "apparent_temperature"
	CLOUDS = "clouds"
	HUMIDITY = "humidity"
	PRECIPITATION = "precipitation"
	PRESSURE = "pressure"
	SNOW_PRECIPITATION = "snow_precipitation"
	TEMPERATURE = "temperature"
	WIND_SPEED = "wind_speed"
	WIND_GUST_SPEED = "wind_gust_speed"

@dataclass(frozen=True, kw_only=True)
class SensorEntityDescription(ComponentSensorEntityDescription):
	value_func: Callable | None = None

SENSORS: Dict[SensorType, SensorEntityDescription] = {
	SensorType.APPARENT_TEMPERATURE: SensorEntityDescription(
		key=SensorType.APPARENT_TEMPERATURE,
		device_class=SensorDeviceClass.TEMPERATURE,
		native_unit_of_measurement=UnitOfTemperature.CELSIUS,
		suggested_display_precision=1,
		state_class=SensorStateClass.MEASUREMENT,
		value_func=lambda actual_weather: actual_weather.apparent_temperature,
	),
	SensorType.CLOUDS: SensorEntityDescription(
		key=SensorType.CLOUDS,
		icon="mdi:weather-partly-cloudy",
		native_unit_of_measurement=PERCENTAGE,
		suggested_display_precision=1,
		state_class=SensorStateClass.MEASUREMENT,
		value_func=lambda actual_weather: actual_weather.clouds,
	),
	SensorType.HUMIDITY: SensorEntityDescription(
		key=SensorType.HUMIDITY,
		device_class=SensorDeviceClass.HUMIDITY,
		native_unit_of_measurement=PERCENTAGE,
		suggested_display_precision=1,
		state_class=SensorStateClass.MEASUREMENT,
		value_func=lambda actual_weather: actual_weather.humidity,
	),
	SensorType.PRECIPITATION: SensorEntityDescription(
		key=SensorType.PRECIPITATION,
		device_class=SensorDeviceClass.PRECIPITATION_INTENSITY,
		native_unit_of_measurement=UnitOfVolumetricFlux.MILLIMETERS_PER_HOUR,
		suggested_display_precision=1,
		state_class=SensorStateClass.MEASUREMENT,
		value_func=lambda actual_weather: actual_weather.precipitation,
	),
	SensorType.PRESSURE: SensorEntityDescription(
		key=SensorType.PRESSURE,
		device_class=SensorDeviceClass.ATMOSPHERIC_PRESSURE,
		native_unit_of_measurement=UnitOfPressure.HPA,
		suggested_display_precision=1,
		state_class=SensorStateClass.MEASUREMENT,
		value_func=lambda actual_weather: actual_weather.pressure,
	),
	SensorType.SNOW_PRECIPITATION: SensorEntityDescription(
		key=SensorType.SNOW_PRECIPITATION,
		icon="mdi:weather-snowy",
		native_unit_of_measurement=PERCENTAGE,
		suggested_display_precision=1,
		state_class=SensorStateClass.MEASUREMENT,
		value_func=lambda actual_weather: actual_weather.snow_precipitation,
	),
	SensorType.TEMPERATURE: SensorEntityDescription(
		key=SensorType.TEMPERATURE,
		device_class=SensorDeviceClass.TEMPERATURE,
		native_unit_of_measurement=UnitOfTemperature.CELSIUS,
		suggested_display_precision=1,
		state_class=SensorStateClass.MEASUREMENT,
		value_func=lambda actual_weather: actual_weather.temperature,
	),
	SensorType.WIND_SPEED: SensorEntityDescription(
		key=SensorType.WIND_SPEED,
		device_class=SensorDeviceClass.WIND_SPEED,
		native_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND,
		suggested_display_precision=1,
		state_class=SensorStateClass.MEASUREMENT,
		value_func=lambda actual_weather: actual_weather.wind_speed,
	),
	SensorType.WIND_GUST_SPEED: SensorEntityDescription(
		key=SensorType.WIND_GUST_SPEED,
		device_class=SensorDeviceClass.WIND_SPEED,
		native_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND,
		suggested_display_precision=1,
		state_class=SensorStateClass.MEASUREMENT,
		value_func=lambda actual_weather: actual_weather.wind_gust_speed,
	),
}

async def async_setup_entry(hass: HomeAssistant, config_entry: AladinOnlineConfigEntry, async_add_entities) -> None:
	coordinator = config_entry.runtime_data

	for sensor_type in SENSORS:
		async_add_entities([
			SensorEntity(coordinator, config_entry.data, SENSORS[sensor_type]),
		])


class SensorEntity(CoordinatorEntity, ComponentSensorEntity):

	entity_description: SensorEntityDescription

	_attr_has_entity_name = True

	def __init__(self, coordinator: DataUpdateCoordinator, config: MappingProxyType, entity_description: SensorEntityDescription):
		super().__init__(coordinator)

		self.entity_description = entity_description
		self._attr_translation_key = entity_description.key

		self._attr_unique_id = "{}.{}".format(
			config[CONF_NAME],
			self.entity_description.key,
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

		self._attr_native_value = self.entity_description.value_func(actual_weather)

	@callback
	def _handle_coordinator_update(self) -> None:
		self._update_attributes()
		super()._handle_coordinator_update()
