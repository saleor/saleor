# Rx Exceptions


class SequenceContainsNoElementsError(Exception):
    def __init__(self, msg=None):
        super(SequenceContainsNoElementsError, self).__init__(msg or "Sequence contains no elements")


class ArgumentOutOfRangeException(ValueError):
    def __init__(self, msg=None):
        super(ArgumentOutOfRangeException, self).__init__(msg or "Argument out of range")


class DisposedException(Exception):
    def __init__(self, msg=None):
        super(DisposedException, self).__init__(msg or "Object has been disposed")


class ReEntracyException(Exception):
    def __init__(self, msg=None):
        super(ReEntracyException, self).__init__(msg or 'Re-entrancy detected')


class CompletedException(Exception):
    def __init__(self, msg=None):
        super(CompletedException, self).__init__(msg or 'Observer completed')


class WouldBlockException(Exception):
    def __init__(self, msg=None):
        super(WouldBlockException, self).__init__(msg or "Would block")


class InvalidOperationException(Exception):
    def __init__(self, msg=None):
        super(InvalidOperationException, self).__init__(msg or "Invalid operation")
