from homeassistant import config_entries, core
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from typing import Final
from .aladin_online import AladinOnlineCoordinator

type AladinOnlineConfigEntry = ConfigEntry[AladinOnlineCoordinator]

PLATFORMS: Final = [
	Platform.SENSOR,
	Platform.WEATHER,
]

async def async_setup_entry(hass: core.HomeAssistant, config_entry: AladinOnlineConfigEntry) -> bool:
	coordinator = AladinOnlineCoordinator(hass, config_entry.data)

	await coordinator.async_config_entry_first_refresh()

	config_entry.runtime_data = coordinator

	await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

	return True

async def async_unload_entry(hass: core.HomeAssistant, config_entry: config_entries.ConfigEntry) -> bool:
	return await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)
