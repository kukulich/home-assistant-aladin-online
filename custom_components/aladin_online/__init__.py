from homeassistant import config_entries, core
from homeassistant.const import Platform
from typing import Final
from .aladin_online import AladinOnlineCoordinator
from .const import DATA_COORDINATOR, DOMAIN

PLATFORMS: Final = [
	Platform.SENSOR,
	Platform.WEATHER,
]

async def async_setup_entry(hass: core.HomeAssistant, config_entry: config_entries.ConfigEntry) -> bool:
	hass.data.setdefault(DOMAIN, {})
	hass.data[DOMAIN][config_entry.entry_id] = {}

	coordinator = AladinOnlineCoordinator(hass, config_entry.data)

	await coordinator.async_config_entry_first_refresh()

	hass.data[DOMAIN][config_entry.entry_id][DATA_COORDINATOR] = coordinator

	await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

	return True

async def async_unload_entry(hass: core.HomeAssistant, config_entry: config_entries.ConfigEntry) -> bool:
	await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)

	hass.data[DOMAIN].pop(config_entry.entry_id)

	return True
