from homeassistant import config_entries, core
from homeassistant.components.sensor import DOMAIN as PLATFORM_SENSOR
from homeassistant.components.weather import DOMAIN as PLATFORM_WEATHER
from .aladin_online import AladinOnlineCoordinator
from .const import DATA_COORDINATOR, DOMAIN


async def async_setup(hass: core.HomeAssistant, config: core.Config) -> bool:
	"""YAML configuration is not supported."""
	return True


async def async_setup_entry(hass: core.HomeAssistant, config_entry: config_entries.ConfigEntry) -> bool:
	hass.data.setdefault(DOMAIN, {})
	hass.data[DOMAIN][config_entry.entry_id] = {}

	coordinator = AladinOnlineCoordinator(hass, config_entry.data)

	await coordinator.async_refresh()

	hass.data[DOMAIN][config_entry.entry_id][DATA_COORDINATOR] = coordinator

	for platform in (PLATFORM_SENSOR, PLATFORM_WEATHER):
		hass.async_create_task(
			hass.config_entries.async_forward_entry_setup(config_entry, platform)
		)

	return True


async def async_unload_entry(hass, config_entry):
	await hass.config_entries.async_forward_entry_unload(config_entry, "weather")
	hass.data[DOMAIN].pop(config_entry.entry_id)

	return True
