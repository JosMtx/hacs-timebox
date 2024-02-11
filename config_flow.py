"""Config flow for Timebox Mini."""
import logging
import re
import voluptuous as vol

from homeassistant import config_entries, exceptions, helpers

from .const import DOMAIN, MAC_REGEX
from .timebox import Timebox

_LOGGER = logging.getLogger(__name__)

async def validate_input(data):
    """Validate the user input allows us to connect."""
    # Check MAC format
    if not re.search(MAC_REGEX, data["mac"]):
        _LOGGER.info("Invalid MAC")
        raise InvalidMac
    # Check connection
    tb = Timebox(data["mac"])
    if not tb.connect():
        _LOGGER.info("Cannot connect to Timebox")
        raise CannotConnect
    tb.disconnect()

class TimeboxConfigFlow(config_entries.ConfigFlow, domain = DOMAIN):
    """Handle a config flow for Timebox."""
    VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        self.data_schema = vol.Schema(
            { vol.Required("mac"): str }
        )

    async def _show_form(self, errors = None):
        """Show the form to the user."""
        return self.async_show_form(step_id = "user", data_schema = self.data_schema, errors = errors)

    async def async_step_user(self, user_input = None):
        """Handle the initial step."""
        if not user_input:
            return await self._show_form()

        # Input provided, validate
        try:
            await validate_input(user_input)
        except CannotConnect:
            return await self._show_form({"base": "cannot_connect"})
        except InvalidMac:
            return await self._show_form({"base": "invalid_mac"})
        except Exception:
            _LOGGER.exception("Unexpected exception")
            return await self._show_form({"base": "unknown"})

        # Check MAC unicity
        mac = helpers.device_registry.format_mac(user_input["mac"])
        await self.async_set_unique_id(mac)
        self._abort_if_unique_id_configured()

        # All good, create entry
        return self.async_create_entry(title = "Timebox", data = {"mac": mac})


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""

class InvalidMac(exceptions.HomeAssistantError):
    """Error to indicate there is an invalid MAC address."""
