import heapq

import rx
from rx.internal.exceptions import InvalidOperationException


class PriorityQueue(object):
    """Priority queue for scheduling"""

    def __init__(self, capacity=None):
        self.items = []
        self.count = 0  # Monotonic increasing for sort stability

        self.lock = rx.config.get("Lock")()

    def __len__(self):
        """Returns length of queue"""

        return len(self.items)

    def peek(self):
        """Returns first item in queue without removing it"""
        try:
            return self.items[0][0]
        except IndexError:
            raise InvalidOperationException("Queue is empty")

    def remove_at(self, index):
        """Removes item at given index"""

        with self.lock:
            item = self.items.pop(index)[0]
            heapq.heapify(self.items)
        return item

    def dequeue(self):
        """Returns and removes item with lowest priority from queue"""

        with self.lock:
            item = heapq.heappop(self.items)[0]
        return item

    def enqueue(self, item):
        """Adds item to queue"""

        with self.lock:
            heapq.heappush(self.items, (item, self.count))
            self.count += 1

    def remove(self, item):
        """Remove given item from queue"""

        with self.lock:
            for index, _item in enumerate(self.items):
                if _item[0] == item:
                    self.items.pop(index)
                    heapq.heapify(self.items)
                    return True

        return False
