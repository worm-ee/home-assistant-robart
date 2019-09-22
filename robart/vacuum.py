"""
Support for Wi-Fi enabled iRobot Roombas.

For more details about this platform, please refer to the documentation
https://home-assistant.io/components/vacuum.roomba/
"""
import asyncio
import logging

import async_timeout
import voluptuous as vol

from homeassistant.components.vacuum import (
    PLATFORM_SCHEMA, SUPPORT_BATTERY, SUPPORT_PAUSE,
    SUPPORT_RETURN_HOME, SUPPORT_SEND_COMMAND, SUPPORT_STATUS, SUPPORT_STOP,
    SUPPORT_TURN_OFF, SUPPORT_TURN_ON, VacuumDevice)
from homeassistant.const import CONF_HOST
from homeassistant.exceptions import PlatformNotReady
import homeassistant.helpers.config_validation as cv
from requests.exceptions import ConnectionError


REQUIREMENTS = ['robart==0.1.1']

_LOGGER = logging.getLogger(__name__)

ATTR_POSITION = 'position'
ATTR_CHARGING = 'charging'
ATTR_UNIQUE_ID = 'unique_id'
ATTR_SOFTWARE_VERSION = 'software_version'

PLATFORM = 'robart'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
}, extra=vol.ALLOW_EXTRA)

# Commonly supported features
SUPPORT_ROBART = SUPPORT_BATTERY | SUPPORT_PAUSE | SUPPORT_RETURN_HOME | \
                 SUPPORT_SEND_COMMAND | SUPPORT_STATUS | SUPPORT_STOP | \
                 SUPPORT_TURN_OFF | SUPPORT_TURN_ON

STATE_CLEANING = "cleaning"
STATE_GOHOME = "go_home"
STATE_NOTREADY = "not_ready"



async def async_setup_platform(
        hass, config, async_add_entities, discovery_info=None):
    """Set up the Robart MyVacBot vacuum cleaner platform."""

    from robart import Robart_MyVacBot, scan

    if PLATFORM not in hass.data:
        hass.data[PLATFORM] = {}
    host = config.get(CONF_HOST)
    _LOGGER.info("Inititalize Robart platform")      
    
    hosts = []
    robot = Robart_MyVacBot(host, '10009')
    try:
      await hass.async_add_job(robot.get_state)
      hosts = [host]
    except ConnectionError:
      hosts = scan(host)
      _LOGGER.error("Robarts on the network %s", hosts)
    
    devices = []
    for host in hosts:
      vacuum = RobartVacuum(host)
      devices.append(vacuum)
      hass.data[PLATFORM][host] = vacuum
      _LOGGER.info("Inititalize Robart %s", host)      

    async_add_entities(devices, True)


class RobartVacuum(VacuumDevice):
    """Representation of a Roomba Vacuum cleaner robot."""

    def __init__(self, host, port='10009'):
        """Initialize the Roomba handler."""

        from robart import Robart_MyVacBot

        self.vacuum_state = None
        self._state_attrs = {}

        self.vacuum = Robart_MyVacBot(host, port)        
        
        try:
          self.vacuum.get_state()
          self.vacuum.get_robotid()
        except ConnectionError:
          self.vacuum_state = None
          _LOGGER.error("Communnication error with %s (%s)", self.vacuum._name, self.vacuum._restCallUrl)      
          return

        self.vacuum_state = self.vacuum._mode

        _LOGGER.info("Vacuum %s (%s)", self.vacuum._name, self.vacuum._restCallUrl)
        _LOGGER.info("mode: {}, charging: {}, battery_level: {}".format(
          self.vacuum._mode, self.vacuum._charging, self.vacuum._battery_level))
        _LOGGER.info('name: {}, unique_id: {}, camlas_unique_id: {}, model: {}, firmware: {}'.format(
          self.vacuum._name, self.vacuum._unique_id, self.vacuum._camlas_unique_id, self.vacuum._model, self.vacuum._firmware))

    @property
    def supported_features(self):
        """Flag vacuum cleaner robot features that are supported."""
        return SUPPORT_ROBART

    @property
    def battery_level(self):
        """Return the battery level of the vacuum cleaner."""
        return self.vacuum._battery_level

    @property
    def status(self):
        """Return the status of the vacuum cleaner."""
        return self.vacuum._mode
#        return "{} / {}".format(self.vacuum._mode, self.vacuum._charging)

    @property
    def is_on(self) -> bool:
        """Return True if entity is on."""
        return self.vacuum._mode == "cleaning"

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.vacuum_state != None

    @property
    def name(self):
        """Return the name of the device."""
        return self.vacuum._name

    @property
    def device_state_attributes(self):
        """Return the state attributes of the device."""
        return self._state_attrs

    async def async_turn_on(self, **kwargs):
        """Turn the vacuum on."""
        await self.hass.async_add_job(self.vacuum.set_clean)

    async def async_turn_off(self, **kwargs):
        """Turn the vacuum off and return to home."""
        await self.hass.async_add_job(self.vacuum.set_home)

    async def async_stop(self, **kwargs):
        """Stop the vacuum cleaner."""
        await self.hass.async_add_job(self.vacuum.set_stop)

    async def async_resume(self, **kwargs):
        """Resume the cleaning cycle."""
        await self.hass.async_add_job(self.vacuum.set_clean)

    async def async_pause(self, **kwargs):
        """Pause the cleaning cycle."""
        await self.hass.async_add_job(self.vacuum.set_stop)

    async def async_start_pause(self, **kwargs):
        """Pause the cleaning task or resume it."""
        await self.hass.async_add_job(self.vacuum.set_clean)

    async def async_return_to_base(self, **kwargs):
        """Set the vacuum cleaner to return to the dock."""
        await self.hass.async_add_job(self.vacuum.set_home)
        
    async def async_update(self):
        """Fetch state from the device."""
        try:
          await self.hass.async_add_job(self.vacuum.get_state)
        except ConnectionError:
          _LOGGER.error("Communnication error with %s (%s)", self.vacuum._name, self.vacuum._restCallUrl)      
          self.vacuum_state = None
          return
        
        self.vacuum_state = self.vacuum._mode
        
        _LOGGER.info("mode: {}, charging: {}, battery_level: {}".format(
          self.vacuum._mode, self.vacuum._charging, self.vacuum._battery_level))


        # Set properties that are to appear in the GUI
        self._state_attrs = {
            ATTR_CHARGING: self.vacuum._charging,
            ATTR_UNIQUE_ID: self.vacuum._unique_id,
            ATTR_SOFTWARE_VERSION: self.vacuum._firmware,
        }

