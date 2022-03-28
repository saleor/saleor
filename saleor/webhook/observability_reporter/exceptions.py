from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .buffer import ObservabilityBuffer


class ObservabilityError(Exception):
    """Common subclass for all Observability exceptions."""


class ObservabilityKombuError(ObservabilityError):
    """Observability Kombu error."""


class ObservabilityConnectionError(ObservabilityError):
    """Observability broker connection error."""


class FullObservabilityBuffer(ObservabilityError):
    def __init__(self, buffer: "ObservabilityBuffer"):
        super().__init__(f"{repr(buffer)} is full.")
