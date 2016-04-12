from collections import deque

__author__ = 'Alex Pinkney'

"""
            __contains__    ordered?
    deque       O(n)          yes
    set         O(1)          no


    Let's combine them!
"""


class SetQueue(object):
    def __init__(self, items=None):
        if not items:
            items = []
        self._set = set(items)
        self._queue = deque(items)

    def __len__(self):
        return len(self._queue)

    def __contains__(self, item):
        return item in self._set

    def add(self, item):
        if item in self._set:
            raise ValueError("Attempting to insert duplicate value %s" % item)
        self._set.add(item)
        self._queue.append(item)

    def remove(self):
        if not len(self._queue):
            raise IndexError("Queue is empty")
        item = self._queue.popleft()
        self._set.remove(item)
        return item

    def peek(self):
        if not len(self._queue):
            raise IndexError("Queue is empty")
        return self._queue[0]
