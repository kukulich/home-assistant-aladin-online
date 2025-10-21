import logging
from typing import Final

LOGGER: Final = logging.getLogger(__package__)

DOMAIN: Final = "aladin_online"
NAME: Final = "Aladin online (Czech Republic)"
URL: Final = "https://aladinonline.oblacno.cz/get_data.php?latitude={}&longitude={}"
