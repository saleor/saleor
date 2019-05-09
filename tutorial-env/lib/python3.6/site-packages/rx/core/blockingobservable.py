from rx.core import ObservableBase


class BlockingObservable(ObservableBase):
    def __init__(self, observable=None):
        """Turns an observable into a blocking observable.

        Keyword arguments:
        :param Observable observable: Observable to make blocking.

        :returns: Blocking observable
        :rtype: BlockingObservable
        """

        self.observable = observable
        super(BlockingObservable, self).__init__()

    def _subscribe_core(self, observer):
        return self.observable.subscribe(observer)
