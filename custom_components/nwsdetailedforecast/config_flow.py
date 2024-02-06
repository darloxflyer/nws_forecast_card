"""Config flow for NWS Detailed Forecast."""
import voluptuous as vol
import logging
from datetime import timedelta

import aiohttp

from homeassistant import config_entries
from homeassistant.const import (
    CONF_API_KEY,
    CONF_LOCATION,
    CONF_MODE,
    CONF_NAME,
    CONF_MONITORED_CONDITIONS,
    CONF_SCAN_INTERVAL,
)
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv

from .const import (
    CONF_LANGUAGE,
    CONFIG_FLOW_VERSION,
    DEFAULT_LANGUAGE,
    DEFAULT_NAME,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    LANGUAGES,
    CONF_UNITS,
    DEFAULT_UNITS,
    ALL_CONDITIONS,
    NWS_PLATFORMS,
    NWS_PLATFORM,
)

ATTRIBUTION = "Powered by the National Weather Forecast"
_LOGGER = logging.getLogger(__name__)

CONF_TWICEDAILY_FORECAST = "twicedaily_forecast"
CONF_STATION_IDENTIFIER = "stationID"
CONF_GRID_IDENTIFIER = "gridCoords"

class NWSDetailedForecastConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for NWS Detailed Forecast."""

    VERSION = CONFIG_FLOW_VERSION

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return NWSDetailedForecastOptionsFlow(config_entry)

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        errors = {}

        schema = vol.Schema(
            {
                vol.Required(CONF_API_KEY): str,
                vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
                vol.Optional(
                    CONF_LOCATION, default=self.hass.config.location_name
                ): cv.location_name,
                vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): int,
                vol.Required(CONF_STATION_IDENTIFIER, default=""): str,
                vol.Required(CONF_GRID_IDENTIFIER, default=""): str,
                vol.Required(NWS_PLATFORM, default=[NWS_PLATFORMS[1]]): cv.multi_select(
                    NWS_PLATFORMS
                ),
                vol.Optional(CONF_TWICEDAILY_FORECAST, default=""): str,
                vol.Optional(CONF_UNITS, default=DEFAULT_UNITS): vol.In(
                    ["si", "us", "ca", "uk"]
                ),
            }
        )

        if user_input is not None:
            station = user_input[CONF_STATION_IDENTIFIER]
            grid = user_input[CONF_GRID_IDENTIFIER]

            # Convert scan interval to timedelta
            if isinstance(user_input[CONF_SCAN_INTERVAL], str):
                user_input[CONF_SCAN_INTERVAL] = cv.time_period_str(
                    user_input[CONF_SCAN_INTERVAL]
                )

            # Convert scan interval to number of seconds
            if isinstance(user_input[CONF_SCAN_INTERVAL], timedelta):
                user_input[CONF_SCAN_INTERVAL] = user_input[
                    CONF_SCAN_INTERVAL
                ].total_seconds()

            # Unique value includes the location and forcastHours/ forecastDays to seperate WeatherEntity/ Sensor
            # await self.async_set_unique_id(f"pw-{latitude}-{longitude}-{forecastDays}-{forecastHours}-{forecastMode}-{entityNamee}")
            await self.async_set_unique_id(
                f"nws-{station}-{grid}"
            )

            self._abort_if_unique_id_configured()

            try:
                api_status = await _is_nws_api_online(
                    self.hass, user_input[CONF_API_KEY], station, grid
                )

                if api_status == 403:
                    _LOGGER.warning(
                        "NWS Detailed Forecast Setup Error: Permission Denied"
                    )
                    errors[
                        "base"
                    ] = "Permission Denied"

            except Exception:
                _LOGGER.warning("NWS Detailed Forecast Setup Error: HTTP Error: " + api_status)
                errors["base"] = "API Error: " + api_status

            if not errors:
                return self.async_create_entry(
                    title=user_input[CONF_NAME], data=user_input
                )
            else:
                _LOGGER.warning(errors)

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_import(self, import_input=None):
        """Set the config entry up from yaml."""
        config = import_input.copy()

        if CONF_NAME not in config:
            config[CONF_NAME] = DEFAULT_NAME
        if CONF_STATION_IDENTIFIER not in config:
            config[CONF_STATION_IDENTIFIER] = ""
        if CONF_GRID_IDENTIFIER not in config:
            config[CONF_GRID_IDENTIFIER] = ""
        if CONF_LANGUAGE not in config:
            config[CONF_LANGUAGE] = DEFAULT_LANGUAGE
        if CONF_UNITS not in config:
            config[CONF_UNITS] = DEFAULT_UNITS
        if CONF_TWICEDAILY_FORECAST not in config:
            config[CONF_TWICEDAILY_FORECAST] = ""
        if CONF_API_KEY not in config:
            config[CONF_API_KEY] = None
        if NWS_PLATFORM not in config:
            config[NWS_PLATFORM] = None
        if CONF_SCAN_INTERVAL not in config:
            config[CONF_SCAN_INTERVAL] = DEFAULT_SCAN_INTERVAL
        return await self.async_step_user(config)


class NWSDetailedForecastOptionsFlow(config_entries.OptionsFlow):
    """Handle options."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_NAME,
                        default=self.config_entry.options.get(
                            CONF_NAME,
                            self.config_entry.data.get(CONF_NAME, DEFAULT_NAME),
                        ),
                    ): str,
                    vol.Optional(
                        CONF_LOCATION,
                        default=self.config_entry.options.get(
                            CONF_LOCATION,
                            self.config_entry.data.get(
                                CONF_LOCATION, self.hass.config.location_name
                            ),
                        ),
                    ): cv.location_name,
                    vol.Required(
                        CONF_STATION_IDENTIFIER,
                        default=self.config_entry.options.get(
                            CONF_STATION_IDENTIFIER,
                            self.config_entry.data.get(
                                CONF_STATION_IDENTIFIER, ""
                            ),
                        ),
                    ): str,
                    vol.Required(
                        CONF_GRID_IDENTIFIER,
                        default=self.config_entry.options.get(
                            CONF_GRID_IDENTIFIER,
                            self.config_entry.data.get(
                                CONF_GRID_IDENTIFIER, ""
                            ),
                        ),
                    ): str,
                    vol.Required(
                        NWS_PLATFORM,
                        default=self.config_entry.options.get(
                            NWS_PLATFORM,
                            self.config_entry.data.get(NWS_PLATFORM, []),
                        ),
                    ): cv.multi_select(NWS_PLATFORMS),
                    vol.Optional(
                        CONF_LANGUAGE,
                        default=self.config_entry.options.get(
                            CONF_LANGUAGE,
                            self.config_entry.data.get(CONF_LANGUAGE, DEFAULT_LANGUAGE),
                        ),
                    ): vol.In(LANGUAGES),
                    vol.Optional(
                        CONF_TWICEDAILY_FORECAST,
                        default=str(
                            self.config_entry.options.get(
                                CONF_TWICEDAILY_FORECAST,
                                self.config_entry.data.get(CONF_HOURLY_FORECAST, ""),
                            ),
                        ),
                    ): str,
                    vol.Optional(
                        CONF_UNITS,
                        default=self.config_entry.options.get(
                            CONF_UNITS,
                            self.config_entry.data.get(CONF_UNITS, DEFAULT_UNITS),
                        ),
                    ): vol.In(["si", "us", "ca", "uk"]),
                }
            ),
        )


async def _is_nws_api_online(hass, api_key, station, grid):
    forecastString = (
        "https://api.weather.gov/gridpoints/"
        + str(station)
        + "/"
        + str(grid)
        + "/forecast"
    )

    async with aiohttp.ClientSession(raise_for_status=False) as session, session.get(
        forecastString
    ) as resp:
        status = resp.status

    return status
