"""Config flow for the Polestar EV platform."""
import asyncio
import logging

from aiohttp import ClientError
from async_timeout import timeout
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME, CONF_USERNAME, CONF_PASSWORD

from .polestar import PolestarApi

from .const import CONF_VIN, CONF_VCC_API_KEY, DOMAIN, TIMEOUT

_LOGGER = logging.getLogger(__name__)


@config_entries.HANDLERS.register(DOMAIN)
class FlowHandler(config_entries.ConfigFlow):
    """Handle a config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def _create_entry(self, username: str, password: str, vin: str, vcc_api_key: str) -> None:
        """Register new entry."""
        return self.async_create_entry(
            title='Polestar EV',
            data={
                CONF_USERNAME: username,
                CONF_PASSWORD: password,
                CONF_VIN: vin,
                CONF_VCC_API_KEY: vcc_api_key
            }
        )

    async def _create_device(self, username: str, password: str, vin: str, vcc_api_key: str):
        """Create device."""

        try:
            device = PolestarApi(
                self.hass,
                username,
                password,
                vin,
                vcc_api_key
            )
            with timeout(TIMEOUT):
                await device.init()
        except asyncio.TimeoutError:
            return self.async_abort(reason="api_timeout")
        except ClientError:
            _LOGGER.exception("ClientError")
            return self.async_abort(reason="api_failed")
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected error creating device")
            return self.async_abort(reason="api_failed")

        return await self._create_entry(username, password, vin, vcc_api_key)

    async def async_step_user(self, user_input=None):
        """User initiated config flow."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=vol.Schema({
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_PASSWORD): str,
                    vol.Required(CONF_VIN): str,
                    vol.Required(CONF_VCC_API_KEY): str,
                })
            )
        return await self._create_device(user_input[CONF_USERNAME], user_input[CONF_PASSWORD], user_input[CONF_VIN], user_input[CONF_VCC_API_KEY])

    async def async_step_import(self, user_input):
        """Import a config entry."""
        return await self._create_device(user_input[CONF_USERNAME], user_input[CONF_PASSWORD], user_input[CONF_VIN], user_input[CONF_VCC_API_KEY])
