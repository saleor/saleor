class LogDrainTransporter:
    abstract = True

    def emit(self, attributes):
        raise NotImplementedError("You must implement emit method for a transporter.")

    def get_endpoint(self):
        raise NotImplementedError(
            "You must implement get_endpoint method for a transporter."
        )
