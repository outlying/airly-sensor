"""
Support for Airly air quality sensors
"""

import asyncio
from datetime import timedelta

import aiohttp
import async_timeout
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.const import (
    CONF_API_KEY, CONF_LATITUDE, CONF_LONGITUDE, ATTR_TEMPERATURE)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA
from homeassistant.helpers.entity import Entity

SCAN_INTERVAL = timedelta(minutes=5)

ATTR_HUMIDITY = 'humidity'
ATTR_PM10 = 'pm_10'
ATTR_PM2_5 = 'pm_2_5'
ATTR_PRESSURE = 'pressure'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_API_KEY): cv.string,
    vol.Optional(CONF_LONGITUDE): cv.longitude,
    vol.Optional(CONF_LATITUDE): cv.latitude
})


class AirlyClient(object):
    """ Airly client """

    def __init__(self, api_key, session=None):
        """
        Constructor

        :param api_key: get one from https://developer.airly.eu/api
        """

        if session is not None:
            self._session = session
        else:
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


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Setup the Airly sensor platform."""

    api_key = config.get(CONF_API_KEY)
    latitude = config.get(CONF_LATITUDE, hass.config.latitude)
    longitude = config.get(CONF_LONGITUDE, hass.config.longitude)

    client = AirlyClient(api_key, async_get_clientsession(hass))
    sensor = AirlySensor(client, longitude, latitude)
    async_add_entities([sensor], True)


class AirlySensor(Entity):
    """Representation of a Airly sensor."""

    def __init__(self, client, longitude, latitude):
        """Initialize the sensor."""
        self._state = None
        self._client = client
        self._longitude = longitude
        self._latitude = latitude

        """ Update upon init """
        self.update()

    @property
    def name(self):
        """Return the name of the sensor."""
        return 'Airly air quality'

    @property
    def state(self):
        """Return the state of the sensor."""
        if self._state is not None:
            return self._state[0]['current']['indexes'][0]['value']
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return 'CAQI'

    @property
    def device_state_attributes(self):
        """Return the state attributes of the last update."""

        attrs = {}

        if self._state is not None:
            current_values_ = self._state[0]['current']['values']
            attrs[ATTR_PRESSURE] = list(filter(self._prop("PRESSURE"), current_values_))[0]['value']
            attrs[ATTR_HUMIDITY] = list(filter(self._prop("HUMIDITY"), current_values_))[0]['value']
            attrs[ATTR_TEMPERATURE] = list(filter(self._prop("TEMPERATURE"), current_values_))[0]['value']
            attrs[ATTR_PM2_5] = list(filter(self._prop("PM25"), current_values_))[0]['value']
            attrs[ATTR_PM10] = list(filter(self._prop("PM10"), current_values_))[0]['value']

        return attrs

    @staticmethod
    def _prop(name):
        """Adds filter for attribute related data"""
        return lambda item: item['name'] == name

    async def update(self):
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        self._state = await self._client.get_state(self._longitude, self._latitude)


# client = AirlyClient("5e55f4d81bdf43478d8ac579827a59e4")
# loop = asyncio.get_event_loop()
# tasks = [client.get_state(50.039700, 19.927633)]
# a = loop.run_until_complete(asyncio.gather(*tasks))
# loop.close()
#
#
# values = a[0]['current']['values']
# print(values)
# print(list(filter(AirlySensor._prop("HUMIDITY"), values))[0]['value'])

