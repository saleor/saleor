class Context(object):
    def __init__(self, **params):
        for key, value in params.items():
            setattr(self, key, value)
