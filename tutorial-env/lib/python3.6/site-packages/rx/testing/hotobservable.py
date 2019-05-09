from rx.core import Observer, AnonymousObserver, ObservableBase, Disposable
from .subscription import Subscription
from .reactive_assert import AssertList


class HotObservable(ObservableBase):
    def __init__(self, scheduler, messages):
        super(HotObservable, self).__init__()

        self.scheduler = scheduler
        self.messages = messages
        self.subscriptions = AssertList()
        self.observers = []

        observable = self

        def get_action(notification):
            def action(scheduler, state):
                for observer in observable.observers[:]:
                    notification.accept(observer)
                return Disposable.empty()
            return action

        for message in self.messages:
            notification = message.value

            # Warning: Don't make closures within a loop
            action = get_action(notification)
            scheduler.schedule_absolute(message.time, action)

    def subscribe(self, on_next=None, on_error=None, on_completed=None, observer=None):
        # Be forgiving and accept an un-named observer as first parameter
        if isinstance(on_next, Observer):
            observer = on_next
        elif not observer:
            observer = AnonymousObserver(on_next, on_error, on_completed)

        return self._subscribe_core(observer)

    def _subscribe_core(self, observer):
        observable = self
        self.observers.append(observer)
        self.subscriptions.append(Subscription(self.scheduler.clock))
        index = len(self.subscriptions) - 1

        def dispose_action():
            observable.observers.remove(observer)
            start = observable.subscriptions[index].subscribe
            end = observable.scheduler.clock
            observable.subscriptions[index] = Subscription(start, end)

        return Disposable.create(dispose_action)
