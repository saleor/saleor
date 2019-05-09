class ActivePlan(object):
    def __init__(self, join_observer_list, on_next, on_completed):
        self.join_observer_list = join_observer_list
        self.on_next = on_next
        self.on_completed = on_completed
        self.join_observers = {}
        for join_observer in self.join_observer_list:
            self.join_observers[join_observer] = join_observer

    def dequeue(self):
        for join_observer in self.join_observers.values():
            join_observer.queue.pop(0)

    def match(self):
        has_values = True
        for join_observer in self.join_observer_list:
            if not len(join_observer.queue):
                has_values = False
                break

        if has_values:
            first_values = []
            is_completed = False
            for join_observer in self.join_observer_list:
                first_values.append(join_observer.queue[0])
                if join_observer.queue[0].kind == 'C':
                    is_completed = True

            if is_completed:
                self.on_completed()
            else:
                self.dequeue()
                values = []
                for value in first_values:
                    values.append(value.value)

                self.on_next(*values)
