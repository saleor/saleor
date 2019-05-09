from rx.core import ObservableBase, Observer, AnonymousObserver, Disposable
from rx.disposables import CompositeDisposable

from .subscription import Subscription
from .reactive_assert import AssertList


class ColdObservable(ObservableBase):
    def __init__(self, scheduler, messages):
        super(ColdObservable, self).__init__()

        self.scheduler = scheduler
        self.messages = messages
        self.subscriptions = AssertList()

    def subscribe(self, on_next=None, on_error=None, on_completed=None, observer=None):
        # Be forgiving and accept an un-named observer as first parameter
        if isinstance(on_next, Observer):
            observer = on_next
        elif not observer:
            observer = AnonymousObserver(on_next, on_error, on_completed)

        return self._subscribe_core(observer)

    def _subscribe_core(self, observer):
        clock = self.scheduler.to_relative(self.scheduler.now)
        self.subscriptions.append(Subscription(clock))
        index = len(self.subscriptions) - 1
        disposable = CompositeDisposable()

        def get_action(notification):
            def action(scheduler, state):
                notification.accept(observer)
                return Disposable.empty()
            return action

        for message in self.messages:
            notification = message.value

            # Don't make closures within a loop
            action = get_action(notification)
            disposable.add(self.scheduler.schedule_relative(message.time, action))

        def dispose():
            start = self.subscriptions[index].subscribe
            end = self.scheduler.to_relative(self.scheduler.now)
            self.subscriptions[index] = Subscription(start, end)
            disposable.dispose()

        return Disposable.create(dispose)
