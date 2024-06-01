import datetime
from homeassistant import config_entries, core
from homeassistant.const import (
	CONF_NAME,
	UnitOfLength,
	UnitOfPressure,
	UnitOfSpeed,
	UnitOfTemperature,
)
from homeassistant.components.weather import (
	ATTR_FORECAST_CLOUD_COVERAGE,
	ATTR_FORECAST_CONDITION,
	ATTR_FORECAST_HUMIDITY,
	ATTR_FORECAST_NATIVE_APPARENT_TEMP,
	ATTR_FORECAST_NATIVE_TEMP,
	ATTR_FORECAST_NATIVE_PRECIPITATION,
	ATTR_FORECAST_NATIVE_PRESSURE,
	ATTR_FORECAST_NATIVE_WIND_GUST_SPEED,
	ATTR_FORECAST_NATIVE_WIND_SPEED,
	ATTR_FORECAST_TIME,
	ATTR_FORECAST_WIND_BEARING,
	Forecast,
	WeatherEntity as ComponentWeatherEntity,
	WeatherEntityFeature,
)
from homeassistant.core import callback, HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator
from homeassistant.helpers.device_registry import DeviceEntryType
from types import MappingProxyType
from . import AladinOnlineConfigEntry
from .aladin_online import AladinActualWeather
from .const import (
	DOMAIN,
	NAME,
)


async def async_setup_entry(hass: HomeAssistant, config_entry: AladinOnlineConfigEntry, async_add_entities) -> None:
	coordinator = config_entry.runtime_data

	async_add_entities([
		WeatherEntity(coordinator, config_entry.data),
	])


class WeatherEntity(CoordinatorEntity, ComponentWeatherEntity):

	_attr_name = None
	_attr_has_entity_name = True
	_attr_native_precipitation_unit = UnitOfLength.MILLIMETERS
	_attr_native_pressure_unit = UnitOfPressure.HPA
	_attr_native_temperature_unit = UnitOfTemperature.CELSIUS
	_attr_native_wind_speed_unit = UnitOfSpeed.METERS_PER_SECOND
	_attr_supported_features = WeatherEntityFeature.FORECAST_HOURLY

	_forecast: list[Forecast] | None = None

	def __init__(self, coordinator: DataUpdateCoordinator, config: MappingProxyType):
		super().__init__(coordinator)

		self._attr_unique_id = "{}.{}".format(
			config[CONF_NAME],
			"hourly",
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

		self._attr_condition = actual_weather.condition
		self._attr_humidity = round(actual_weather.humidity, 1)
		self._attr_native_pressure = round(actual_weather.pressure, 1)
		self._attr_native_temperature = round(actual_weather.temperature, 1)
		self._attr_native_wind_speed = round(actual_weather.wind_speed, 1)
		self._attr_wind_bearing = round(actual_weather.wind_bearing, 2)
		self._attr_native_wind_gust_speed = round(actual_weather.wind_gust_speed, 1)
		self._attr_native_apparent_temperature = round(actual_weather.apparent_temperature, 1)
		self._attr_cloud_coverage = int(round(actual_weather.clouds))

		now = datetime.datetime.now()

		self._forecast: list[Forecast] = []

		for hourly_forecast in self.coordinator.data.hourly_forecasts:
			if hourly_forecast.datetime < now:
				continue

			self._forecast.append({
				ATTR_FORECAST_TIME: hourly_forecast.datetime.isoformat(),
				ATTR_FORECAST_CONDITION: hourly_forecast.condition,
				ATTR_FORECAST_CLOUD_COVERAGE: int(round(hourly_forecast.clouds)),
				ATTR_FORECAST_HUMIDITY: hourly_forecast.humidity,
				ATTR_FORECAST_NATIVE_APPARENT_TEMP: round(hourly_forecast.apparent_temperature, 1),
				ATTR_FORECAST_NATIVE_TEMP: round(hourly_forecast.temperature, 1),
				ATTR_FORECAST_NATIVE_PRECIPITATION: round(hourly_forecast.precipitation, 1),
				ATTR_FORECAST_NATIVE_PRESSURE: round(hourly_forecast.pressure, 1),
				ATTR_FORECAST_NATIVE_WIND_SPEED: round(hourly_forecast.wind_speed, 1),
				ATTR_FORECAST_WIND_BEARING: round(hourly_forecast.wind_bearing, 2),
				ATTR_FORECAST_NATIVE_WIND_GUST_SPEED: round(hourly_forecast.wind_gust_speed, 1),
			})

	async def async_forecast_hourly(self) -> list[Forecast] | None:
		return self._forecast

	@callback
	def _handle_coordinator_update(self) -> None:
		self._update_attributes()
		super()._handle_coordinator_update()
