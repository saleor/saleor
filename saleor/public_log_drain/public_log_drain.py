from .transporters import LogDrainTransporter


class PublicLogDrain:
    def __init__(self):
        self.transporters: list[LogDrainTransporter] = []

    def add_transporter(self, transporter):
        self.transporters.append(transporter)

    def emit_log(self, attributes):
        for transporter in self.transporters:
            transporter.emit(attributes)

    def get_transporters(self):
        return self.transporters
