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
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from typing import List
from .aladin_online import AladinWeather
from .const import (
	DOMAIN,
	DATA_COORDINATOR,
	NAME,
)


async def async_setup_entry(hass: core.HomeAssistant, config_entry: config_entries.ConfigEntry, async_add_entities) -> None:
	coordinator = hass.data[DOMAIN][config_entry.entry_id][DATA_COORDINATOR]

	async_add_entities([
		WeatherEntity(coordinator, config_entry.data),
	])


class WeatherEntity(CoordinatorEntity, ComponentWeatherEntity):

	def __init__(self, coordinator, config):
		super().__init__(coordinator)

		self._config = config

	@property
	def unique_id(self) -> str:
		return "{}.{}".format(
			self._config[CONF_NAME],
			"hourly",
		)

	@property
	def name(self) -> str:
		return self._config[CONF_NAME]

	@property
	def condition(self) -> str:
		return self._weather.actual_weather.condition

	@property
	def temperature(self) -> float:
		return self._weather.actual_weather.temperature

	@property
	def temperature_unit(self) -> str:
		return TEMP_CELSIUS

	@property
	def pressure(self) -> float:
		return self._weather.actual_weather.pressure

	@property
	def humidity(self) -> float:
		return self._weather.actual_weather.humidity

	@property
	def wind_speed(self) -> float:
		return self._weather.actual_weather.wind_speed

	@property
	def wind_bearing(self) -> float:
		return self._weather.actual_weather.wind_bearing

	@property
	def attribution(self):
		return None

	@property
	def forecast(self) -> List[dict]:
		forecast = []

		now = datetime.datetime.now()

		for hourly_forecast in self._weather.hourly_forecasts:
			if (hourly_forecast.datetime < now):
				continue

			forecast.append({
				ATTR_FORECAST_TIME: hourly_forecast.datetime,
				ATTR_FORECAST_CONDITION: hourly_forecast.condition,
				ATTR_FORECAST_TEMP: hourly_forecast.temperature,
				ATTR_FORECAST_PRECIPITATION: hourly_forecast.precipitation,
				ATTR_FORECAST_WIND_SPEED: hourly_forecast.wind_speed,
				ATTR_FORECAST_WIND_BEARING: hourly_forecast.wind_bearing,
			})

		return forecast

	@property
	def device_info(self):
		return {
			"identifiers": {(DOMAIN,)},
			"model": "Weather forecast",
			"default_name": "Weather forecast",
			"manufacturer": NAME,
			"entry_type": "service",
		}

	@property
	def _weather(self) -> AladinWeather:
		return self.coordinator.data
