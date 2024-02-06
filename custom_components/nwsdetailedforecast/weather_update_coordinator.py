"""Weather updater for NWS Detailed Forecast service."""
import logging

import async_timeout
from forecastio.models import Forecast
import json
import aiohttp


from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed


from .const import (
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

ATTRIBUTION = "Powered by the National Weather Service"


class WeatherUpdateCoordinator(DataUpdateCoordinator):
    """Weather data update coordinator."""

    def __init__(self, api_key, station, grid, pw_scan_Int, hass):
        """Initialize coordinator."""
        self._api_key = api_key
        self.station = station
        self.grid = grid
        self.pw_scan_Int = pw_scan_Int

        self.data = None
        self.currently = None
        self.hourly = None
        self.daily = None
        self._connect_error = False

        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=pw_scan_Int)

    async def _async_update_data(self):
        """Update the data."""
        data = {}
        async with async_timeout.timeout(60):
            try:
                data = await self._get_pw_weather()
                _LOGGER.info(
                    "NWS Detailed Update data update for "
                    + str(self.station)
                    + ","
                    + str(self.grid)
                )
            except Exception as err:
                raise UpdateFailed(f"Error communicating with API: {err}")
        return data

    async def _get_pw_weather(self):
        """Poll weather data from NWS."""

        forecastString = (
            "https://api.weather.gov/gridpoints/"
            + str(self.station)
            + "/"
            + str(self.grid)
            + "/forecast"
        )

        async with aiohttp.ClientSession(raise_for_status=True) as session, session.get(
            forecastString
        ) as resp:
            resptext = await resp.text()
            jsonText = json.loads(resptext)
            headers = resp.headers
            status = resp.raise_for_status()

            data = Forecast(jsonText, status, headers)
        return data