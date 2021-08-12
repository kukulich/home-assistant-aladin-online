import datetime
from homeassistant import config_entries, core
from homeassistant.components.weather import (
	ATTR_FORECAST_CONDITION,
	ATTR_FORECAST_TEMP,
	ATTR_FORECAST_PRECIPITATION,
	ATTR_FORECAST_TIME,
	ATTR_FORECAST_WIND_BEARING,
	ATTR_FORECAST_WIND_SPEED,
	WeatherEntity as ComponentWeatherEntity,
)
from homeassistant.const import (
	CONF_NAME,
	TEMP_CELSIUS,
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

DEVICE_INFO: Final[DeviceInfo] = {
	"identifiers": {(DOMAIN,)},
	"model": "Weather forecast",
	"default_name": "Weather forecast",
	"manufacturer": NAME,
	"entry_type": "service",
}


async def async_setup_entry(hass: core.HomeAssistant, config_entry: config_entries.ConfigEntry, async_add_entities) -> None:
	coordinator = hass.data[DOMAIN][config_entry.entry_id][DATA_COORDINATOR]

	async_add_entities([
		WeatherEntity(coordinator, config_entry.data),
	])


class WeatherEntity(CoordinatorEntity, ComponentWeatherEntity):

	_attr_temperature_unit = TEMP_CELSIUS

	def __init__(self, coordinator: DataUpdateCoordinator, config: MappingProxyType):
		super().__init__(coordinator)

		self._attr_unique_id = "{}.{}".format(
			config[CONF_NAME],
			"hourly",
		)

		self._attr_name = config[CONF_NAME]

		self._attr_device_info = DEVICE_INFO

		self._update_attributes()

	def _update_attributes(self):
		actual_weather: AladinActualWeather = self.coordinator.data.actual_weather

		self._attr_condition = actual_weather.condition
		self._attr_humidity = actual_weather.humidity
		self._attr_pressure = actual_weather.pressure
		self._attr_temperature = actual_weather.temperature
		self._attr_wind_bearing = actual_weather.wind_bearing
		self._attr_wind_speed = actual_weather.wind_speed_in_kilometers_per_hour

		now = datetime.datetime.now()

		self._attr_forecast = []

		for hourly_forecast in self.coordinator.data.hourly_forecasts:
			if hourly_forecast.datetime < now:
				continue

			self._attr_forecast.append({
				ATTR_FORECAST_TIME: hourly_forecast.datetime,
				ATTR_FORECAST_CONDITION: hourly_forecast.condition,
				ATTR_FORECAST_TEMP: hourly_forecast.temperature,
				ATTR_FORECAST_PRECIPITATION: hourly_forecast.precipitation,
				ATTR_FORECAST_WIND_SPEED: hourly_forecast.wind_speed_in_kilometers_per_hour,
				ATTR_FORECAST_WIND_BEARING: hourly_forecast.wind_bearing,
			})

	@callback
	def _handle_coordinator_update(self) -> None:
		self._update_attributes()
		super()._handle_coordinator_update()
