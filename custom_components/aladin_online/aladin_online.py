from datetime import datetime, timedelta
from homeassistant import core
from homeassistant.components.weather import (
    ATTR_CONDITION_CLEAR_NIGHT,
    ATTR_CONDITION_CLOUDY,
    ATTR_CONDITION_PARTLYCLOUDY,
    ATTR_CONDITION_POURING,
    ATTR_CONDITION_SNOWY,
    ATTR_CONDITION_SUNNY,
    ATTR_CONDITION_RAINY,
    ATTR_CONDITION_WINDY,
)
from homeassistant.const import (
    CONF_LATITUDE,
    CONF_LONGITUDE,
)
from homeassistant.helpers import aiohttp_client
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt
from http import HTTPStatus
import math
from .const import (
    DOMAIN,
    LOGGER,
    CONF_STATION_ID,
    URL,
)
from .errors import NoData, ServiceUnavailable
from types import MappingProxyType
from typing import Final, List

# Nová URL - data-provider.chmi.cz, parametr je ID stanice
URL: Final = "https://data-provider.chmi.cz/api/graphs/graf.meteogram/{}"

# Mapování číselných ikon na HA podmínky
# Vzor: 10=jasno den, 110=jasno noc, 20=skoro jasno den, 120=skoro jasno noc
# 40=polojasno, 140=polojasno noc, 60=skoro zataženo, 70=zataženo+déšť
# 80=zataženo, 81=zataženo+déšť, 160=polojasno noc, 170=skoro zataženo noc
ICON_CONDITION_MAP = {
    10:  ATTR_CONDITION_SUNNY,          # jasno den
    20:  ATTR_CONDITION_SUNNY,          # skoro jasno den
    40:  ATTR_CONDITION_PARTLYCLOUDY,   # polojasno
    60:  ATTR_CONDITION_CLOUDY,         # skoro zataženo
    70:  ATTR_CONDITION_RAINY,          # zataženo + déšť
    80:  ATTR_CONDITION_CLOUDY,         # zataženo
    81:  ATTR_CONDITION_POURING,        # zataženo + silný déšť
    110: ATTR_CONDITION_CLEAR_NIGHT,    # jasno noc
    120: ATTR_CONDITION_CLEAR_NIGHT,    # skoro jasno noc
    140: ATTR_CONDITION_PARTLYCLOUDY,   # polojasno noc
    160: ATTR_CONDITION_PARTLYCLOUDY,   # skoro zataženo noc
    170: ATTR_CONDITION_CLOUDY,         # zataženo noc
}


class AladinActualWeather:

    def __init__(
        self,
        condition: str,
        temperature: float,
        apparent_temperature: float,
        precipitation: float,
        pressure: float,
        humidity: float,
        clouds: float,
        wind_speed: float,
        wind_bearing: float,
        wind_gust_speed: float,
        wind_gust_bearing: float,
        snow_precipitation: float,
    ) -> None:
        self.condition = condition
        self.temperature = temperature
        self.apparent_temperature = apparent_temperature
        self.precipitation = precipitation
        self.pressure = pressure
        self.humidity = humidity
        self.clouds = clouds
        self.wind_speed = wind_speed
        self.wind_bearing = wind_bearing
        self.wind_gust_speed = wind_gust_speed
        self.wind_gust_bearing = wind_gust_bearing
        self.snow_precipitation = snow_precipitation


class AladinWeatherForecast:

    def __init__(
        self,
        forecast_datetime: datetime,
        condition: str,
        temperature: float,
        apparent_temperature: float,
        precipitation: float,
        pressure: float,
        wind_speed: float,
        wind_bearing: float,
        wind_gust_speed: float,
        humidity: float,
        clouds: float,
    ) -> None:
        self.datetime = forecast_datetime
        self.condition = condition
        self.temperature = temperature
        self.apparent_temperature = apparent_temperature
        self.precipitation = precipitation
        self.pressure = pressure
        self.wind_speed = wind_speed
        self.wind_bearing = wind_bearing
        self.wind_gust_speed = wind_gust_speed
        self.humidity = humidity
        self.clouds = clouds


class AladinWeather:

    def __init__(self, actual_weather: AladinActualWeather) -> None:
        self.actual_weather: AladinActualWeather = actual_weather
        self.hourly_forecasts: List[AladinWeatherForecast] = []

    def add_hourly_forecast(self, forecast: AladinWeatherForecast) -> None:
        self.hourly_forecasts.append(forecast)


class AladinOnlineCoordinator(DataUpdateCoordinator):

    def __init__(self, hass: core.HomeAssistant, config: MappingProxyType) -> None:
        super().__init__(hass, LOGGER, name=DOMAIN, update_interval=timedelta(minutes=30), update_method=self.update)

        self._config: MappingProxyType = config
        self._data = None

    async def update(self) -> AladinWeather:
        if self._should_update_data():
            try:
                await self._update_data()
            except Exception as ex:
                if self._data is None:
                    raise ex

        if self._data is None:
            raise ServiceUnavailable

        entries = self._data.get("data", [])
        if not entries:
            raise NoData

        now = datetime.now(tz=dt.UTC)

        # Najdi aktuální hodinu v datech
        actual_entry = None
        actual_index = 0
        for i, entry in enumerate(entries):
            entry_time = dt.parse_datetime(entry["validityTime"])
            if entry_time <= now:
                actual_entry = entry
                actual_index = i
            else:
                break

        if actual_entry is None:
            actual_entry = entries[0]
            actual_index = 0

        actual_weather = AladinActualWeather(
            condition=AladinOnlineCoordinator._format_condition(actual_entry.get("icon", 0)),
            temperature=actual_entry.get("t2m"),
            apparent_temperature=actual_entry.get("t2m"),   # nové API apparent_temp nemá, fallback na t2m
            precipitation=actual_entry.get("prec", 0),
            pressure=actual_entry.get("mslp"),              # už v hPa, nepřepočítávat
            humidity=actual_entry.get("rh2m"),              # už v %, nepřepočítávat
            clouds=actual_entry.get("cloudsTot"),            # už v %, nepřepočítávat
            wind_speed=actual_entry.get("windSpeed", 0),
            wind_bearing=AladinOnlineCoordinator._format_wind_direction(actual_entry.get("windDirection", 0)),
            wind_gust_speed=actual_entry.get("windGustSpeed", 0),
            wind_gust_bearing=AladinOnlineCoordinator._format_wind_direction(actual_entry.get("windDirection", 0)),
            snow_precipitation=actual_entry.get("snow", 0),
        )

        weather = AladinWeather(actual_weather)

        for entry in entries[actual_index + 1:]:
            forecast_datetime = dt.parse_datetime(entry["validityTime"])

            forecast = AladinWeatherForecast(
                forecast_datetime=forecast_datetime,
                condition=AladinOnlineCoordinator._format_condition(entry.get("icon", 0)),
                temperature=entry.get("t2m"),
                apparent_temperature=entry.get("t2m"),
                precipitation=entry.get("prec", 0),
                pressure=entry.get("mslp"),
                wind_speed=entry.get("windSpeed", 0),
                wind_bearing=AladinOnlineCoordinator._format_wind_direction(entry.get("windDirection", 0)),
                wind_gust_speed=entry.get("windGustSpeed", 0),
                humidity=entry.get("rh2m"),
                clouds=entry.get("cloudsTot"),
            )
            weather.add_hourly_forecast(forecast)

        return weather

    def _should_update_data(self) -> bool:
        if self._data is None:
            return True
        # ČHMÚ aktualizuje 4x denně: 00, 06, 12, 18 UTC
        if datetime.now().hour in [1, 7, 13, 19]:
            return True
        return False

    async def _update_data(self) -> None:
        session = aiohttp_client.async_get_clientsession(self.hass)
        station_id = self._config.get(CONF_STATION_ID, 98)
        response = await session.get(URL.format(station_id))

        if response.status != HTTPStatus.OK:
            raise ServiceUnavailable

        self._data = await response.json(content_type=None)

    @staticmethod
    def _format_condition(icon: int) -> str:
        if icon in ICON_CONDITION_MAP:
            return ICON_CONDITION_MAP[icon]
        LOGGER.warning("Neznámá ikona počasí: {}".format(icon))
        return ATTR_CONDITION_SUNNY

    @staticmethod
    def _format_wind_direction(raw: float) -> float:
        return (raw + 180) % 360
