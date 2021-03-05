from homeassistant.exceptions import HomeAssistantError


class AladinOnlineException(HomeAssistantError):
    """Base class for exceptions."""


class ServiceUnavailable(AladinOnlineException):
    """Service is not available."""


class LocationUnavailable(AladinOnlineException):
    """Location is not available."""


class NoData(AladinOnlineException):
    """No data."""
