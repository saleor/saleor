class ObservabilityError(Exception):
    pass


class ConnectionDoesNotExist(ObservabilityError):
    pass


class ConnectionInterrupted(ObservabilityError):
    pass


class CompressorError(ObservabilityError):
    pass
