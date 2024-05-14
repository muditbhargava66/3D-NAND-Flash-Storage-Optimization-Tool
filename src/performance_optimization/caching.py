# src/performance_optimization/caching.py

from collections import OrderedDict

class CachingSystem:
    def __init__(self, capacity=1024):
        self.capacity = capacity
        self.cache = OrderedDict()

    def get(self, key):
        if key not in self.cache:
            return None
        self.cache.move_to_end(key)
        return self.cache[key]

    def put(self, key, value):
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)

    def clear(self):
        self.cache.clear()
        
    def invalidate(self, cache_key):
        # implement the logic to invalidate the cache for the given key
        # for example, you can remove the key from the cache dictionary
        if cache_key in self.cache:
            del self.cache[cache_key]