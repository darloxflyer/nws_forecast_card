"""Support for NWS Detailed Forecast"""
import logging

from dataclasses import dataclass, field

import voluptuous as vol
import homeassistant.helpers.config_validation as cv
import homeassistant.helpers.template as template_helper


from homeassistant.components.sensor import (
    PLATFORM_SCHEMA,
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from typing import Literal, NamedTuple

from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.typing import DiscoveryInfoType

from homeassistant.const import (
    ATTR_ATTRIBUTION,
    CONF_API_KEY,
    CONF_LOCATION,
    CONF_NAME,
    CONF_SCAN_INTERVAL,
    Platform,
    DEGREE,
    PERCENTAGE,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
    UnitOfLength,
    UnitOfVolumetricFlux,
    UnitOfPrecipitationDepth,
    UV_INDEX,
)

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

_LOGGER = logging.getLogger(__name__)

ATTRIBUTION = "Powered by the National Weather Service"

CONF_TWICEDAILY_FORECAST = "twicedaily_forecast"
CONF_LANGUAGE = "language"
CONF_UNITS = "units"

DEFAULT_LANGUAGE = "en"
DEFAULT_NAME = "NWSDetailedForecast"

DEPRECATED_SENSOR_TYPES = {
    "apparent_temperature_max",
    "apparent_temperature_min",
    "temperature_max",
    "temperature_min",
}

MAP_UNIT_SYSTEM: dict[
    Literal["si", "us", "ca", "uk", "uk2"],
    Literal["si_unit", "us_unit", "ca_unit", "uk_unit", "uk2_unit"],
] = {
    "si": "si_unit",
    "us": "us_unit",
    "ca": "ca_unit",
    "uk": "uk_unit",
    "uk2": "uk2_unit",
}


@dataclass
class NWSDetailedForecastSensorEntityDescription(SensorEntityDescription):
    """Describes Pirate Weather sensor entity."""

    si_unit: str | None = None
    us_unit: str | None = None
    ca_unit: str | None = None
    uk_unit: str | None = None
    uk2_unit: str | None = None
    forecast_mode: list[str] = field(default_factory=list)


# Sensor Types
SENSOR_TYPES: dict[str, NWSDetailedForecastSensorEntityDescription] = {
    "shortForecast": NWSDetailedForecastSensorEntityDescription(
        key="shortForecast",
        name="Short Forecast",
        forecast_mode=["twicedaily"],
    ),
    "detailedForecast": NWSDetailedForecastSensorEntityDescription(
        key="detailedForecast",
        name="Detailed Forecast",
        forecast_mode=["twicedaily"],
    ),
    "icon": NWSDetailedForecastSensorEntityDescription(
        key="icon",
        name="Icon",
        forecast_mode=["twicedaily"],
    ),
    "precip_probability": NWSDetailedForecastSensorEntityDescription(
        key="probabilityOfPrecipitation",
        name="Precip Probability",
        si_unit=PERCENTAGE,
        us_unit=PERCENTAGE,
        ca_unit=PERCENTAGE,
        uk_unit=PERCENTAGE,
        uk2_unit=PERCENTAGE,
        suggested_display_precision=0,
        icon="mdi:water-percent",
        forecast_mode=["twicedaily"],
    ),
    "temperature": NWSDetailedForecastSensorEntityDescription(
        key="temperature",
        name="Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        si_unit=UnitOfTemperature.CELSIUS,
        us_unit=UnitOfTemperature.FAHRENHEIT,
        ca_unit=UnitOfTemperature.CELSIUS,
        uk_unit=UnitOfTemperature.CELSIUS,
        uk2_unit=UnitOfTemperature.CELSIUS,
        suggested_display_precision=2,
        forecast_mode=["twicedaily"],
    ),
    "dewpoint": NWSDetailedForecastSensorEntityDescription(
        key="dewpoint",
        name="Dew Point",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        si_unit=UnitOfTemperature.CELSIUS,
        us_unit=UnitOfTemperature.FAHRENHEIT,
        ca_unit=UnitOfTemperature.CELSIUS,
        uk_unit=UnitOfTemperature.CELSIUS,
        uk2_unit=UnitOfTemperature.CELSIUS,
        suggested_display_precision=2,
        forecast_mode=["twicedaily"],
    ),
    "windSpeed": NWSDetailedForecastSensorEntityDescription(
        key="windSpeed",
        name="Wind Speed",
        device_class=SensorDeviceClass.WIND_SPEED,
        icon="mdi:weather-windy",
        forecast_mode=["twicedaily"],
    ),
    "windDirection": NWSDetailedForecastSensorEntityDescription(
        key="windDirection",
        name="Wind Direction",
        icon="mdi:compass",
        forecast_mode=["twicedaily"],
    ),
    "relativeHumidity": NWSDetailedForecastSensorEntityDescription(
        key="relativeHumidity",
        name="Relative Humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
        si_unit=PERCENTAGE,
        us_unit=PERCENTAGE,
        ca_unit=PERCENTAGE,
        uk_unit=PERCENTAGE,
        uk2_unit=PERCENTAGE,
        suggested_display_precision=0,
        forecast_mode=["twicedaily"],
    ),
    "alerts": NWSDetailedForecastSensorEntityDescription(
        key="alerts",
        name="Alerts",
        icon="mdi:alert-circle-outline",
        forecast_mode=[],
    ),
    "time": NWSDetailedForecastSensorEntityDescription(
        key="time",
        name="Time",
        icon="mdi:clock-time-three-outline",
        forecast_mode=["twicedaily"],
    ),
}


class ConditionPicture(NamedTuple):
    """Entity picture and icon for condition."""

    entity_picture: str
    icon: str


CONDITION_PICTURES: dict[str, ConditionPicture] = {
    "clear-day": ConditionPicture(
        entity_picture="/static/images/darksky/weather-sunny.svg",
        icon="mdi:weather-sunny",
    ),
    "clear-night": ConditionPicture(
        entity_picture="/static/images/darksky/weather-night.svg",
        icon="mdi:weather-night",
    ),
    "rain": ConditionPicture(
        entity_picture="/static/images/darksky/weather-pouring.svg",
        icon="mdi:weather-pouring",
    ),
    "snow": ConditionPicture(
        entity_picture="/static/images/darksky/weather-snowy.svg",
        icon="mdi:weather-snowy",
    ),
    "sleet": ConditionPicture(
        entity_picture="/static/images/darksky/weather-hail.svg",
        icon="mdi:weather-snowy-rainy",
    ),
    "wind": ConditionPicture(
        entity_picture="/static/images/darksky/weather-windy.svg",
        icon="mdi:weather-windy",
    ),
    "fog": ConditionPicture(
        entity_picture="/static/images/darksky/weather-fog.svg",
        icon="mdi:weather-fog",
    ),
    "cloudy": ConditionPicture(
        entity_picture="/static/images/darksky/weather-cloudy.svg",
        icon="mdi:weather-cloudy",
    ),
    "partly-cloudy-day": ConditionPicture(
        entity_picture="/static/images/darksky/weather-partlycloudy.svg",
        icon="mdi:weather-partly-cloudy",
    ),
    "partly-cloudy-night": ConditionPicture(
        entity_picture="/static/images/darksky/weather-cloudy.svg",
        icon="mdi:weather-night-partly-cloudy",
    ),
}


# Language Supported Codes
LANGUAGE_CODES = [
    "en",
]

ALLOWED_UNITS = ["auto", "si", "us", "ca", "uk", "uk2"]

ALERTS_ATTRS = ["time", "description", "expires", "severity", "uri", "regions", "title"]

HOURS = list(range(168))
DAYS = list(range(7))

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
        vol.Optional(CONF_TWICEDAILY_FORECAST): cv.multi_select(HOURS),
    }
)


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

    # Define as a sensor platform
    config_entry[NWS_PLATFORM] = [NWS_PLATFORMS[0]]

    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_IMPORT}, data=config_entry
        )
    )


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up NWS Detailed Forecast sensor entities based on a config entry."""

    domain_data = hass.data[DOMAIN][config_entry.entry_id]

    name = domain_data[CONF_NAME]
    weather_coordinator = domain_data[ENTRY_WEATHER_COORDINATOR]
    conditions = domain_data[CONF_MONITORED_CONDITIONS]
    forecast_twicedaily = domain_data[CONF_TWICEDAILY_FORECAST]

    sensors: list[NWSDetailedForecastSensor] = []

    for condition in conditions:
        # Save units for conversion later
        requestUnits = domain_data[CONF_UNITS]

        sensorDescription = SENSOR_TYPES[condition]

        if condition in DEPRECATED_SENSOR_TYPES:
            _LOGGER.warning("Monitored condition %s is deprecated", condition)

        if (
            not sensorDescription.forecast_mode
            or "currently" in sensorDescription.forecast_mode
        ):
            unique_id = f"{config_entry.unique_id}-sensor-{condition}"
            sensors.append(
                NWSDetailedForecastSensor(
                    weather_coordinator,
                    condition,
                    name,
                    unique_id,
                    forecast_twicedaily=None,
                    description=sensorDescription,
                    requestUnits=requestUnits,
                )
            )

        if forecast_twicedaily is not None and "twicedaily" in sensorDescription.forecast_mode:
            for forecast_h in forecast_hours:
                unique_id = (
                    f"{config_entry.unique_id}-sensor-{condition}-hourly-{forecast_h}"
                )
                sensors.append(
                    NWSDetailedForecastSensor(
                        weather_coordinator,
                        condition,
                        name,
                        unique_id,
                        forecast_twicedaily=int(forecast_h),
                        description=sensorDescription,
                        requestUnits=requestUnits,
                    )
                )

    async_add_entities(sensors)


class NWSDetailedForecastSensor(SensorEntity):
    """Class for an NWS Detailed Forecast sensor."""

    # _attr_should_poll = False
    _attr_attribution = ATTRIBUTION
    entity_description: NWSDetailedForecastSensorEntityDescription

    def __init__(
        self,
        weather_coordinator: WeatherUpdateCoordinator,
        condition: str,
        name: str,
        unique_id,
        forecast_twicedaily: int,
        description: NWSDetailedForecastSensorEntityDescription,
        requestUnits: str,
    ) -> None:
        """Initialize the sensor."""
        self.client_name = name

        description = description
        self.entity_description = description
        self.description = description

        self._weather_coordinator = weather_coordinator

        self._attr_unique_id = unique_id
        self._attr_name = name

        self.forecast_twicedaily = forecast_twicedaily
        self.requestUnits = requestUnits
        self.type = condition
        self._icon = None
        self._alerts = None

        self._name = description.name

    @property
    def name(self):
        """Return the name of the sensor."""
        if self.forecast_twicedaily is not None:
            return f"{self.client_name} {self._name} {self.forecast_twicedaily}h"
        return f"{self.client_name} {self._name}"

    @property
    def available(self) -> bool:
        """Return if weather data is available from PirateWeather."""
        return self._weather_coordinator.data is not None

    @property
    def attribution(self):
        """Return the attribution."""
        return ATTRIBUTION

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        unit_key = MAP_UNIT_SYSTEM.get(self.unit_system, "si_unit")
        self._attr_native_unit_of_measurement = getattr(
            self.entity_description, unit_key
        )
        return self._attr_native_unit_of_measurement

    @property
    def unit_system(self):
        """Return the unit system of this entity."""
        return self.requestUnits

    @property
    def entity_picture(self) -> str | None:
        """Return the entity picture to use in the frontend, if any."""
        if self._icon is None or "summary" not in self.entity_description.key:
            return None

        if self._icon in CONDITION_PICTURES:
            return CONDITION_PICTURES[self._icon].entity_picture

        return None

    def update_unit_of_measurement(self) -> None:
        """Update units based on unit system."""
        unit_key = MAP_UNIT_SYSTEM.get(self.unit_system, "si_unit")
        self._attr_native_unit_of_measurement = getattr(
            self.entity_description, unit_key
        )

    @property
    def icon(self) -> str | None:
        """Icon to use in the frontend, if any."""
        if (
            "summary" in self.entity_description.key
            and self._icon in CONDITION_PICTURES
        ):
            return CONDITION_PICTURES[self._icon].icon

        return self.entity_description.icon

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        if self.type == "alerts":
            extraATTR = self._alerts
            extraATTR[ATTR_ATTRIBUTION] = ATTRIBUTION

            return extraATTR
        else:
            return {ATTR_ATTRIBUTION: ATTRIBUTION}

    @property
    def native_value(self) -> StateType:
        """Return the state of the device."""

        self.update_unit_of_measurement()

        if self.type == "alerts":
            data = self._weather_coordinator.data.alerts()

            alerts = {}
            if data is None:
                self._alerts = alerts
                return data

            multiple_alerts = len(data) > 1
            for i, alert in enumerate(data):
                for attr in ALERTS_ATTRS:
                    if multiple_alerts:
                        dkey = f"{attr}_{i!s}"
                    else:
                        dkey = attr
                    alertsAttr = getattr(alert, attr)

                    # Convert time to string
                    if isinstance(alertsAttr, int):
                        alertsAttr = template_helper.timestamp_local(alertsAttr)

                    alerts[dkey] = alertsAttr

            self._alerts = alerts
            native_val = len(data)

        elif self.type == "twicedaily_summary":
            native_val = getattr(self._weather_coordinator.data.daily(), "shortForecast", "")
            self._icon = getattr(self._weather_coordinator.data.daily(), "icon", "")

        else:
            currently = self._weather_coordinator.data.currently()
            native_val = self.get_state(currently.d)

        # self._state = native_val

        return native_val

    def get_state(self, data):
        """Return a new state based on the type.

        If the sensor type is unknown, the current state is returned.
        """
        lookup_type = convert_to_camel(self.type)
        state = data.get(lookup_type)

        if state is None:
            return state

        if "shortForecast" in self.type:
            self._icon = getattr(data, "icon", "")

        # Some state data needs to be rounded to whole values or converted to
        # percentages
        # NWS ALREADY PRESENTS THIS INFORMATION IN WHOLE INTEGERS
        #if self.type in ["probabilityOfPrecipitation", "relativeHumidity"]:
        #    state = state * 100

        # Logic to convert from SI to requsested units for compatability
        # Temps in F
        if self.requestUnits in ["us"]:
            if self.type in [
                "dewpoint",
                "temperature",
            ]:
                state = (state * 9 / 5) + 32

        if self.type in [
            "dew_point",
            "temperature",
            "apparent_temperature",
            "temperature_low",
            "apparent_temperature_low",
            "temperature_min",
            "apparent_temperature_min",
            "temperature_high",
            "apparent_temperature_high",
            "temperature_max",
            "apparent_temperature_max",
            "precip_accumulation",
            "pressure",
            "ozone",
            "uvIndex",
            "wind_speed",
            "wind_gust",
        ]:
            if roundingVal == 0:
                outState = int(round(state, roundingVal))
            else:
                outState = state

        else:
            outState = state

        return outState

    async def async_added_to_hass(self) -> None:
        """Connect to dispatcher listening for entity data notifications."""
        self.async_on_remove(
            self._weather_coordinator.async_add_listener(self.async_write_ha_state)
        )

    # async def async_update(self) -> None:
    #    """Get the latest data from PW and updates the states."""
    #    await self._weather_coordinator.async_request_refresh()


def convert_to_camel(data):
    """Convert snake case (foo_bar_bat) to camel case (fooBarBat).

    This is not pythonic, but needed for certain situations.
    """
    components = data.split("_")
    capital_components = "".join(x.title() for x in components[1:])
    return f"{components[0]}{capital_components}"