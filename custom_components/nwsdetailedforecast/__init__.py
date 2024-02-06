"""The NWS Detailed Forecast component."""
from __future__ import annotations

import logging

from typing   import Any
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry

from homeassistant.const import (
    CONF_API_KEY,
    CONF_LOCATION,
    CONF_MODE,
    CONF_NAME,
    CONF_MONITORED_CONDITIONS,
    CONF_SCAN_INTERVAL,
)
from homeassistant.core import HomeAssistant

from .const import (
    DOMAIN,
    ENTRY_NAME,
    ENTRY_WEATHER_COORDINATOR,
    PLATFORMS,
    UPDATE_LISTENER,
    CONF_UNITS,
    NWS_PLATFORMS,
    NWS_PLATFORM,
)

from .weather_update_coordinator import WeatherUpdateCoordinator

CONF_TWICEDAILY_FORECAST = "twicedaily_forecast"
CONF_STATION_IDENTIFIER = "stationID"
CONF_GRID_IDENTIFIER = "gridCoords"

_LOGGER = logging.getLogger(__name__)
ATTRIBUTION = "Powered by the National Weather Service"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up NWS Detailed Weather as config entry."""
    name = entry.data[CONF_NAME]
    api_key = entry.data[CONF_API_KEY]
    location = entry.data.get(CONF_LOCATION, hass.config.location_name)
    station = _get_config_value(entry, CONF_STATION_IDENTIFIER)
    grid = _get_config_value(entry, CONF_GRID_IDENTIFIER)
    forecast_twicedaily = _get_config_value(entry, CONF_TWICEDAILY_FORECAST)
    nws_entity_platform = _get_config_value(entry, NWS_PLATFORM)
    nws_scan_Int = entry.data[CONF_SCAN_INTERVAL]

    # _LOGGER.warning(forecast_days)
    if isinstance(forecast_twicedaily, str):
        # If empty, set to none
        if forecast_twicedaily == "" or forecast_twicedaily == "None":
            forecast_twicedaily = None
        else:
            if forecast_twicedaily[0] == "[":
                forecast_twicedaily = forecast_twicedaily[1:-1].split(",")
            else:
                forecast_twicedaily = forecast_twicedaily.split(",")
            forecast_twicedaily = [int(i) for i in forecast_twicedaily]

    unique_location = f"nws-{location}"

    hass.data.setdefault(DOMAIN, {})
    # Create and link weather WeatherUpdateCoordinator
    weather_coordinator = WeatherUpdateCoordinator(
        api_key, station, grid, timedelta(seconds=nws_scan_Int), hass
    )
    hass.data[DOMAIN][unique_location] = weather_coordinator

    # await weather_coordinator.async_refresh()
    await weather_coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        ENTRY_NAME: name,
        ENTRY_WEATHER_COORDINATOR: weather_coordinator,
        CONF_API_KEY: api_key,
        CONF_STATION_IDENTIFIER: station,
        CONF_GRID_IDENTIFIER: grid,
        CONF_UNITS: units,
        CONF_TWICEDAILY_FORECAST: forecast_twicedaily,
        NWS_PLATFORM: nws_entity_platform,
        CONF_SCAN_INTERVAL: nws_scan_Int,
    }

    # If both platforms
    if (NWS_PLATFORMS[0] in nws_entity_platform) and (
        NWS_PLATFORMS[1] in nws_entity_platform
    ):
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    # If only sensor
    elif NWS_PLATFORMS[0] in nws_entity_platform:
        await hass.config_entries.async_forward_entry_setup(entry, PLATFORMS[0])
    # If only weather
    elif NWS_PLATFORMS[1] in nws_entity_platform:
        await hass.config_entries.async_forward_entry_setup(entry, PLATFORMS[1])

    update_listener = entry.add_update_listener(async_update_options)
    hass.data[DOMAIN][entry.entry_id][UPDATE_LISTENER] = update_listener
    return True


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    nws_entity_prevplatform = hass.data[DOMAIN][entry.entry_id][NWS_PLATFORM]

    # If both
    if (NWS_PLATFORMS[0] in nws_entity_prevplatform) and (
        NWS_PLATFORMS[1] in nws_entity_prevplatform
    ):
        unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    # If only sensor
    elif NWS_PLATFORMS[0] in nws_entity_prevplatform:
        unload_ok = await hass.config_entries.async_unload_platforms(
            entry, [PLATFORMS[0]]
        )
    # If only Weather
    elif NWS_PLATFORMS[1] in nws_entity_prevplatform:
        unload_ok = await hass.config_entries.async_unload_platforms(
            entry, [PLATFORMS[1]]
        )

    _LOGGER.info("Unloading NWS Detailed Forecast")

    if unload_ok:
        update_listener = hass.data[DOMAIN][entry.entry_id][UPDATE_LISTENER]
        update_listener()

        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


def _get_config_value(config_entry: ConfigEntry, key: str) -> Any:
    if config_entry.options:
        return config_entry.options[key]
    return config_entry.data[key]


def _filter_domain_configs(elements, domain):
    return list(filter(lambda elem: elem["platform"] == domain, elements))
