"""
Support for Airly air quality sensors
"""

import asyncio

import aiohttp
import async_timeout
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.const import (
    CONF_API_KEY, CONF_LATITUDE, CONF_LONGITUDE)
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA
from homeassistant.helpers.entity import Entity

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_API_KEY): cv.string,
    vol.Optional(CONF_LONGITUDE): cv.longitude,
    vol.Optional(CONF_LATITUDE): cv.latitude
})


class AirlyClient(object):
    """ Airly client """

    def __init__(self, api_key):
        """
        Constructor

        :param api_key: get one from https://developer.airly.eu/api
        """

        self._session = aiohttp.ClientSession()
        self._timeout = 20
        self._headers = {
            'Accept': 'application/json',
            'apikey': api_key
        }

    @asyncio.coroutine
    def get_state(self, latitude, longitude):
        """Get air quality status for coordinates"""
        return (yield from self._get(
            'https://airapi.airly.eu/v2/measurements/point?lat={}&lng={}'.format(latitude, longitude)))

    @asyncio.coroutine
    def _get(self, path, **kwargs):
        with async_timeout.timeout(self._timeout):
            resp = yield from self._session.get(
                path, params=dict(self._headers, **kwargs))
            return (yield from resp.json())


with AirlyClient("5e55f4d81bdf43478d8ac579827a59e4") as client:
    print(client.get_state(123, 123))


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Setup the Airly sensor platform."""

    api_key = config.get(CONF_API_KEY)
    latitude = config.get(CONF_LATITUDE, hass.config.latitude)
    longitude = config.get(CONF_LONGITUDE, hass.config.longitude)

    async_add_entities([AirlySensor()])


class AirlySensor(Entity):
    """Representation of a Airly sensor."""

    def __init__(self):
        """Initialize the sensor."""
        self._state = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return 'Airly air quality'

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return 'CAQI'

    @property
    def device_state_attributes(self):
        """Return the state attributes of the last update."""

        attrs = {}

        return attrs

    async def update(self):
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        self._state = 23
