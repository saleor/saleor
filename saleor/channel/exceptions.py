class ChannelNotDefined(Exception):
    def __init__(self, msg=None):
        if msg is None:
            msg = "More than one channel exists. Specify which channel to use."
        super().__init__(msg)


class NoDefaultChannel(Exception):
    def __init__(self, msg=None):
        if msg is None:
            msg = "A default channel does not exist."
        super().__init__(msg)
