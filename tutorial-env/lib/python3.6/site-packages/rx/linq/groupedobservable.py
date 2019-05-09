from rx import AnonymousObservable
from rx.core import ObservableBase
from rx.disposables import CompositeDisposable


class GroupedObservable(ObservableBase):
    def __init__(self, key, underlying_observable, merged_disposable=None):
        super(GroupedObservable, self).__init__()
        self.key = key

        def subscribe(observer):
            return CompositeDisposable(merged_disposable.disposable, underlying_observable.subscribe(observer))

        self.underlying_observable = underlying_observable if not merged_disposable else AnonymousObservable(subscribe)

    def _subscribe_core(self, observer):
        return self.underlying_observable.subscribe(observer)
