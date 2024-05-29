from abc import ABC, abstractmethod


class LogDrainTransporter(ABC):
    @abstractmethod
    def emit(self, logger_name: str, trace_id: int, span_id: int, attributes):
        pass

    @abstractmethod
    def get_endpoint(self):
        pass
