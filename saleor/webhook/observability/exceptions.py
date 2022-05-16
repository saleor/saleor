class ObservabilityError(Exception):
    pass


class ConnectionNotConfigured(ObservabilityError):
    pass


class ConnectionInterrupted(ObservabilityError):
    pass


class CompressorError(ObservabilityError):
    pass
