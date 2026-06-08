import logging
from typing import Final

LOGGER: Final = logging.getLogger(__package__)
DOMAIN: Final = "aladin_online"
NAME: Final = "Aladin online EK (Czech Republic)"
URL: Final = "https://data-provider.chmi.cz/api/graphs/graf.meteogram/{}"
CONF_STATION_ID: Final = "station_id"
