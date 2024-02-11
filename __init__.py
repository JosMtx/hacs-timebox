"""The Timebox Mini integration."""
import logging
import voluptuous as vol
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN
from .timebox import Timebox

_LOGGER = logging.getLogger(__name__)

# ~ CONFIG_SCHEMA = vol.Schema({vol.Required("mac"): str})
CONFIG_SCHEMA = cv.removed(DOMAIN, raise_if_present=False)

async def async_setup_entry(hass, entry):
    """Set up from a config entry."""
    _LOGGER.info("setting up entry")
    mac = entry.data["mac"]
    hass.data[DOMAIN] = Timebox(mac)
    await hass.async_add_executor_job(setup_hass_services, hass)
    return True


async def async_unload_entry(hass, entry):
    """Unload a config entry."""
    _LOGGER.info("unloading entry")
    hass.services.async_remove(DOMAIN, "show_time")
    hass.services.async_remove(DOMAIN, "show_weather")
    hass.services.async_remove(DOMAIN, "set_volume")
    hass.services.async_remove(DOMAIN, "set_brightness")
    hass.services.async_remove(DOMAIN, "show_image")
    hass.data.pop(DOMAIN)
    return True

def setup_hass_services(hass):

    def show_time(call):
        _LOGGER.info("show time")
        hass.states.set("timebox.display", "time")
        tb = hass.data[DOMAIN]
        tb.connect()
        tb.show_time()
        tb.disconnect()

    def show_weather(call):
        _LOGGER.info("show weather")
        hass.states.set("timebox.display", "weather")
        tb = hass.data[DOMAIN]
        tb.connect()
        tb.show_weather()
        tb.disconnect()

    def set_volume(call):
        vol = call.data["volume"]
        _LOGGER.info("set volume to %d", vol)
        tb = hass.data[DOMAIN]
        tb.connect()
        tb.set_volume(vol)
        tb.disconnect()

    def set_brightness(call):
        bri = call.data["brightness"]
        _LOGGER.info("set brightness to %d", bri)
        tb = hass.data[DOMAIN]
        tb.connect()
        tb.set_brightness(bri)
        tb.disconnect()

    def show_image(call):
        img = call.data["image"]
        _LOGGER.info("show image %s", img)
        hass.states.set("timebox.display", "image")
        tb = hass.data[DOMAIN]
        tb.connect()
        tb.show_image(img)
        tb.disconnect()

    _LOGGER.info("installing services")
    hass.services.register(DOMAIN, "show_time", show_time)
    hass.services.register(DOMAIN, "show_weather", show_weather)
    hass.services.register(DOMAIN, "set_volume", set_volume)
    hass.services.register(DOMAIN, "set_brightness", set_brightness)
    hass.services.register(DOMAIN, "show_image", show_image)

    # Return boolean to indicate that initialization was successful.
    return True
