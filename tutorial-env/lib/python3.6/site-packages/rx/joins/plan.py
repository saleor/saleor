from .activeplan import ActivePlan
from .joinobserver import JoinObserver


class Plan(object):
    def __init__(self, expression, selector):
        self.expression = expression
        self.selector = selector

    def activate(self, external_subscriptions, observer, deactivate):
        join_observers = []
        for pattern in self.expression.patterns:
            join_observers.append(self.plan_create_observer(external_subscriptions, pattern, observer.on_error))

        def on_next(*args):
            try:
                result = self.selector(*args)
            except Exception as e:
                observer.on_error(e)
                return
            observer.on_next(result)

        def on_completed():
            for join_observer in join_observers:
                join_observer.remove_active_plan(active_plan)

            deactivate(active_plan)

        active_plan = ActivePlan(join_observers, on_next, on_completed)

        for join_observer in join_observers:
            join_observer.add_active_plan(active_plan)

        return active_plan

    def plan_create_observer(self, external_subscriptions, observable, on_error):
        entry = external_subscriptions.get(observable)
        if not entry:
            observer = JoinObserver(observable, on_error)
            external_subscriptions[observable] = observer
            return observer

        return entry
