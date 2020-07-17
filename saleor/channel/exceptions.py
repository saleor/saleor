class ChannelSlugNotPassedException(Exception):
    def __init__(self, msg=None):
        if msg is None:
            msg = "Channel slug not passed."
        super().__init__(msg)


class NoChannelException(Exception):
    def __init__(self, msg=None):
        if msg is None:
            msg = "There's no channel."
        super().__init__(msg)
