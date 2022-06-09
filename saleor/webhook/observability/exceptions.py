class ObservabilityError(Exception):
    pass


class ConnectionNotConfigured(ObservabilityError):
    pass


class TruncationError(ObservabilityError):
    pass
