from rx import AnonymousObservable
from rx.core import ObservableBase, Disposable
from rx.disposables import CompositeDisposable


class ConnectableObservable(ObservableBase):
    """Represents an observable that can be connected and disconnected."""

    def __init__(self, source, subject):
        self.subject = subject
        self.source = source.as_observable()
        self.has_subscription = False
        self.subscription = None

        super(ConnectableObservable, self).__init__()

    def _subscribe_core(self, observer):
        return self.subject.subscribe(observer)

    def connect(self):
        """Connects the observable."""

        if not self.has_subscription:
            self.has_subscription = True

            def dispose():
                self.has_subscription = False

            disposable = self.source.subscribe(self.subject)
            self.subscription = CompositeDisposable(disposable, Disposable.create(dispose))

        return self.subscription

    def ref_count(self):
        """Returns an observable sequence that stays connected to the
        source as long as there is at least one subscription to the
        observable sequence.
        """

        connectable_subscription = [None]
        count = [0]
        source = self

        def subscribe(observer):
            count[0] += 1
            should_connect = count[0] == 1
            subscription = source.subscribe(observer)
            if should_connect:
                connectable_subscription[0] = source.connect()

            def dispose():
                subscription.dispose()
                count[0] -= 1
                if not count[0]:
                    connectable_subscription[0].dispose()

            return Disposable.create(dispose)

        return AnonymousObservable(subscribe)

    def auto_connect(self, subscriber_count=1):
        """Returns an observable sequence that stays connected to the
        source indefinitely to the observable sequence.
        Providing a subscriber_count will cause it to connect() after that many subscriptions occur.
        A subscriber_count of 0 will result in emissions firing immediately without waiting for subscribers.
        """

        connectable_subscription = [None]
        count = [0]
        source = self
        is_connected = [False]

        if subscriber_count == 0:
            connectable_subscription[0] = source.connect()
            is_connected[0] = True

        def subscribe(observer):
            count[0] += 1
            should_connect = count[0] == subscriber_count and not is_connected[0]
            subscription = source.subscribe(observer)
            if should_connect:
                connectable_subscription[0] = source.connect()
                is_connected[0] = True

            def dispose():
                subscription.dispose()
                count[0] -= 1
                is_connected[0] = False

            return Disposable.create(dispose)

        return AnonymousObservable(subscribe)
