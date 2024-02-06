"""Support for the NWS Detailed Forecast service."""
from __future__ import annotations

import logging

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.util.dt import utc_from_timestamp
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.core import HomeAssistant, callback
from .weather_update_coordinator import WeatherUpdateCoordinator
from homeassistant.helpers.typing import DiscoveryInfoType


from homeassistant.components.weather import (
    ATTR_CONDITION_CLEAR_NIGHT,
    ATTR_CONDITION_CLOUDY,
    ATTR_CONDITION_FOG,
    ATTR_CONDITION_HAIL,
    ATTR_CONDITION_LIGHTNING,
    ATTR_CONDITION_PARTLYCLOUDY,
    ATTR_CONDITION_RAINY,
    ATTR_CONDITION_SNOWY,
    ATTR_CONDITION_SNOWY_RAINY,
    ATTR_CONDITION_SUNNY,
    ATTR_CONDITION_WINDY,
    ATTR_CONDITION_EXCEPTIONAL,
    PLATFORM_SCHEMA,
    Forecast,
    WeatherEntityFeature,
    SingleCoordinatorWeatherEntity,
)


from homeassistant.const import (
    CONF_API_KEY,
    CONF_LOCATION,
    CONF_MODE,
    CONF_NAME,
    CONF_SCAN_INTERVAL,
    UnitOfPrecipitationDepth,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
    UnitOfLength,
)

from .const import (
    DEFAULT_NAME,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    ENTRY_NAME,
    ENTRY_WEATHER_COORDINATOR,
    PLATFORMS,
    UPDATE_LISTENER,
    CONF_UNITS,
    NWS_PLATFORMS,
    NWS_PLATFORM,
)

_LOGGER = logging.getLogger(__name__)

ATTRIBUTION = "Powered by the National weather Service"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_API_KEY): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_UNITS): vol.In(ALLOWED_UNITS),
        vol.Optional(CONF_LANGUAGE, default=DEFAULT_LANGUAGE): vol.In(LANGUAGE_CODES),
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): cv.time_period,
        vol.Optional(CONF_LOCATION, default=""): cv.location,
        vol.Required(CONF_STATION_IDENTIFIER, default=""): str,
        vol.Required(CONF_GRID_IDENTIFIER, default=""): str,
        vol.Optional(NWS_PLATFORM): cv.multi_select(NWS_PLATFORMS),
        vol.Optional(CONF_MODE, default="twicedaily"): vol.In(FORECAST_MODES),
    }
)


MAP_CONDITION = {
    "clear-day": ATTR_CONDITION_SUNNY,
    "clear-night": ATTR_CONDITION_CLEAR_NIGHT,
    "rain": ATTR_CONDITION_RAINY,
    "snow": ATTR_CONDITION_SNOWY,
    "sleet": ATTR_CONDITION_SNOWY_RAINY,
    "wind": ATTR_CONDITION_WINDY,
    "fog": ATTR_CONDITION_FOG,
    "cloudy": ATTR_CONDITION_CLOUDY,
    "partly-cloudy-day": ATTR_CONDITION_PARTLYCLOUDY,
    "partly-cloudy-night": ATTR_CONDITION_PARTLYCLOUDY,
    "hail": ATTR_CONDITION_HAIL,
    "thunderstorm": ATTR_CONDITION_LIGHTNING,
    "tornado": ATTR_CONDITION_EXCEPTIONAL,
}

CONF_UNITS = "units"

DEFAULT_NAME = "NWS Detailed Forecast"


async def async_setup_platform(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Import the platform into a config entry."""
    _LOGGER.warning(
        "Configuration of NWS Detailed Forecast in YAML is deprecated "
        "Your existing configuration has been imported into the UI automatically "
        "and can be safely removed from your configuration.yaml file"
    )

    # Add source to config
    config_entry[NWS_PLATFORM] = [NWS_PLATFORMS[1]]

    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_IMPORT}, data=config_entry
        )
    )


def _map_twicedaily_forecast(forecast) -> Forecast:
    return {
        "datetime": utc_from_timestamp(forecast.d.get("startTime")).isoformat(),
        "condition": forecast.d.get("shortForecast"),
        "native_temperature": forecast.d.get("temperature"),
        "native_dew_point": forecast.d.get("dewpoint").get("value"),
        "native_wind_speed": forecast.d.get("windSpeed"),
        "wind_bearing": forecast.d.get("windDirection"),
        "humidity": forecast.d.get("relativeHumidity").get("value"),
        "precipitation_probability": forecast.d.get("probabilityOfPrecipitation").get("value"),
    }


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up NWS Detailed Forecast entity based on a config entry."""
    domain_data = hass.data[DOMAIN][config_entry.entry_id]
    name = domain_data[CONF_NAME]
    weather_coordinator = domain_data[ENTRY_WEATHER_COORDINATOR]
    forecast_mode = domain_data[CONF_MODE]

    unique_id = f"{config_entry.unique_id}"

    nws_weather = NWSDetailedForecast(
        name, unique_id, forecast_mode, weather_coordinator
    )

    async_add_entities([nws_weather], False)
    # _LOGGER.info(pw_weather.__dict__)


class NWSDetailedForecast(SingleCoordinatorWeatherEntity[WeatherUpdateCoordinator]):
    """Implementation of an NWSDetailedForecast sensor."""

    _attr_attribution = ATTRIBUTION
    _attr_should_poll = False

    _attr_native_temperature_unit = UnitOfTemperature.FAHRENHEIT

    def __init__(
        self,
        name: str,
        unique_id,
        forecast_mode: str,
        weather_coordinator: WeatherUpdateCoordinator,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(weather_coordinator)
        self._attr_name = name
        # self._attr_device_info = DeviceInfo(
        #    entry_type=DeviceEntryType.SERVICE,
        #    identifiers={(DOMAIN, unique_id)},
        #    manufacturer=MANUFACTURER,
        #    name=DEFAULT_NAME,
        # )
        self._weather_coordinator = weather_coordinator
        self._name = name
        self._mode = forecast_mode
        self._unique_id = unique_id
        self._ds_twicedaily = self._weather_coordinator.data.twicedaily()

    @property
    def unique_id(self):
        """Return a unique_id for this entity."""
        return self._unique_id

    @property
    def supported_features(self) -> WeatherEntityFeature:
        """Determine supported features based on available data sets reported by WeatherKit."""
        features = WeatherEntityFeature(0)

        features |= WeatherEntityFeature.FORECAST_TWICEDAILY
        return features

    @property
    def available(self):
        """Return if weather data is available from PirateWeather."""
        return self._weather_coordinator.data is not None

    @property
    def attribution(self):
        """Return the attribution."""
        return ATTRIBUTION

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def native_temperature(self):
        """Return the temperature."""
        temperature = self._weather_coordinator.data.currently().d.get("temperature")

        return round(temperature, 2)

    @property
    def relativeHumidity(self):
        """Return the humidity."""
        humidity = self._weather_coordinator.data.currently().d.get("relativeHumidity").get("value")

        return humidity

    @property
    def native_wind_speed(self):
        """Return the wind speed."""
        windspeed = self._weather_coordinator.data.currently().d.get("windSpeed")

    @property
    def windDirection(self):
        """Return the wind bearing."""
        return self._weather_coordinator.data.currently().d.get("windDirection")

    @property
    def condition(self):
        """Return the weather condition."""

        return self._weather_coordinator.data.currently().d.get("shortForecast")

    @callback
    def _async_forecast_twicedaily(self) -> list[Forecast] | None:
        """Return the twicedaily forecast."""
        twicedaily_forecast = self._weather_coordinator.data.twicedaily().data
        if not twicedaily_forecast:
            return None

        return [_map_twicedaily_forecast(f) for f in twicedaily_forecast]

    async def async_update(self) -> None:
        """Get the latest data from NWS and updates the states."""
        await self._weather_coordinator.async_request_refresh()

    async def async_added_to_hass(self) -> None:
        """Connect to dispatcher listening for entity data notifications."""
        self.async_on_remove(
            self._weather_coordinator.async_add_listener(self.async_write_ha_state)
        )
