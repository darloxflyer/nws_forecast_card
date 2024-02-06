"""Consts for the NWS Detailed Forecasts."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntityDescription,
    SensorStateClass,
)

from homeassistant.components.weather import (
    ATTR_FORECAST_CONDITION,
    ATTR_FORECAST_PRECIPITATION_PROBABILITY,
    ATTR_FORECAST_TEMP,
    ATTR_FORECAST_TIME,
    ATTR_FORECAST_HUMIDITY,
    ATTR_FORECAST_DEW_POINT,
    ATTR_FORECAST_WIND_SPEED,
    ATTR_FORECAST_WIND_BEARING,
)
from homeassistant.const import (
    DEGREE,
    UnitOfLength,
    PERCENTAGE,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
    UV_INDEX,
    Platform,
)

DOMAIN = "nwsdetailedforecast"
DEFAULT_NAME = "NWSDetailedForecast"
DEFAULT_LANGUAGE = "en"
DEFAULT_UNITS = "us"
DEFAULT_SCAN_INTERVAL = 3600
ATTRIBUTION = "Data provided by NWS Forecast API"
MANUFACTURER = "NWS"
CONF_LANGUAGE = "language"
CONF_UNITS = "units"
CONFIG_FLOW_VERSION = 2
ENTRY_NAME = "name"
ENTRY_WEATHER_COORDINATOR = "weather_coordinator"
ATTR_API_PERIODNUMBER = "number"
ATTR_API_PERIODNAME = "name"
ATTR_API_PRECIPITATION = "probabilityOfPrecipitation"
ATTR_API_STARTTIME = "startTime"
ATTR_API_ENDTIME = "endTime"
ATTR_API_DEW_POINT = "dewpoint"
ATTR_API_TEMPERATURE = "temperature"
ATTR_API_FEELS_LIKE_TEMPERATURE = "feels_like_temperature"
ATTR_API_WIND_SPEED = "windSpeed"
ATTR_API_WIND_DIRECTION = "windDirection"
ATTR_API_HUMIDITY = "relativeHumidity"
ATTR_API_SHORTFORECAST = "shortForecast"
ATTR_API_DETAILEDFORECAST = "detailedForecast"
ATTR_API_NWSICONURL = "icon"
UPDATE_LISTENER = "update_listener"
PLATFORMS = [Platform.SENSOR, Platform.WEATHER]
NWS_PLATFORMS = ["Sensor", "Weather"]
NWS_PLATFORM = "nws_detailed_platform"

ALL_CONDITIONS = {
    "probabilityOfPrecipitation": "Precipitation Probability",
    "temperature": "Temperature",
    "dewpoint": "Dew Point",
    "relativeHumidity": "Relative Humidity",
    "windSpeed": "Wind Speed",
    "windDirection": "Wind Direction",
    "shortForecast" : "Short Forecast",
    "detailedForecast" : "Detailed Forecast"
    "updated": "Updated At",
}

LANGUAGES = [
    "en",
]


FORECAST_SENSOR_TYPES: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key=ATTR_FORECAST_PRECIPITATION_PROBABILITY,
        name="Precipitation probability",
        native_unit_of_measurement=PERCENTAGE,
    ),
    SensorEntityDescription(
        key=ATTR_FORECAST_TEMP,
        name="Temperature",
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        device_class=SensorDeviceClass.TEMPERATURE,
    ),
    SensorEntityDescription(
        key=ATTR_FORECAST_DEW_POINT,
        name="Dew Point",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
    ),
    SensorEntityDescription(
        key=ATTR_FORECAST_HUMIDITY,
        name="Relative Humidity",
        native_unit_of_measurement=PERCENTAGE,
    ),
    SensorEntityDescription(
        key=ATTR_FORECAST_TIME,
        name="Time",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    SensorEntityDescription(
        key=ATTR_API_WIND_SPEED,
        name="Wind Speed",
    ),
    SensorEntityDescription(
        key=ATTR_API_WIND_DIRECTION,
        name="Wind Direction",
    ),
    SensorEntityDescription(
        key=ATTR_API_SHORTFORECAST,
        name="Short Forecast",
    ),
    SensorEntityDescription(
        key=ATTR_API_DETAILEDFORECAST,
        name="Detailed Forecast",
    ),
    SensorEntityDescription(
        key=ATTR_API_PERIODNUMBER,
        name="Period Number",
    ),
    SensorEntityDescription(
        key=ATTR_API_PERIODNAME,
        name="Period Name",
    ),
    SensorEntityDescription(
        key=ATTR_API_NWSICONURL,
        name="NWS Icon URL",
    ),

)