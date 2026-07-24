class NoDefaultCustomerType(Exception):
    def __init__(self, msg=None):
        if msg is None:
            msg = "The default customer type does not exist."
        super().__init__(msg)
