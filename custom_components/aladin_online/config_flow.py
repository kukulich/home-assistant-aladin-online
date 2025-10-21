from __future__ import annotations
from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.data_entry_flow import AbortFlow, FlowResult
from homeassistant.helpers import aiohttp_client
from http import HTTPStatus
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from .const import DOMAIN, NAME, URL, LOGGER, CONF_STATION_ID
from .errors import ServiceUnavailable
from typing import Any, Dict

class AladinOnlineConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
	"""Weather forecast config flow."""

	async def async_step_user(self, user_input: Dict[str, Any] | None = None) -> FlowResult:
		errors = {}
		if user_input is not None:
			try:
				config = {
					CONF_NAME: user_input[CONF_NAME],
					CONF_STATION_ID: user_input[CONF_STATION_ID],
				}
				await self.async_set_unique_id(user_input[CONF_NAME])
				self._abort_if_unique_id_configured()

				await self._async_validate_station(user_input[CONF_STATION_ID])

				return self.async_create_entry(title=NAME, data=config)
			except AbortFlow as ex:
				return self.async_abort(reason=ex.reason)
			except ServiceUnavailable:
				errors["base"] = "service_unavailable"
			except Exception:
				LOGGER.error("Unknown error connecting to %s", URL.format(user_input[CONF_STATION_ID]))
				return self.async_abort(reason="unknown")

		return self.async_show_form(
			step_id="user",
			data_schema=vol.Schema({
				vol.Required(CONF_NAME, default=self.hass.config.location_name): str,
				vol.Required(CONF_STATION_ID): int,
			}),
			errors=errors,
		)

	async def async_step_reconfigure(self, user_input: Dict[str, Any] | None = None) -> FlowResult:
		errors = {}
		reconfigure_entry = self._get_reconfigure_entry()
		if user_input is not None:
			try:
				config = {
					CONF_NAME: reconfigure_entry.data[CONF_NAME],
					CONF_STATION_ID: user_input[CONF_STATION_ID],
				}

				await self._async_validate_station(user_input[CONF_STATION_ID])

				return self.async_update_reload_and_abort(reconfigure_entry, data=config)
			except AbortFlow as ex:
				return self.async_abort(reason=ex.reason)
			except ServiceUnavailable:
				errors["base"] = "service_unavailable"
			except Exception:
				LOGGER.error("Unknown error connecting to %s", URL.format(user_input[CONF_STATION_ID]))
				return self.async_abort(reason="unknown")

		if CONF_STATION_ID in reconfigure_entry.data:
			station_id_field = vol.Required(CONF_STATION_ID, default=reconfigure_entry.data[CONF_STATION_ID])
		else:
			station_id_field = vol.Required(CONF_STATION_ID)

		return self.async_show_form(
			step_id="reconfigure",
			data_schema=vol.Schema({
				station_id_field: int,
			}),
			errors=errors,
		)

	async def _async_validate_station(self, station_id: int) -> None:
		session = aiohttp_client.async_get_clientsession(self.hass)
		response = await session.get(URL.format(station_id))
		if response.status != HTTPStatus.OK:
			raise ServiceUnavailable
