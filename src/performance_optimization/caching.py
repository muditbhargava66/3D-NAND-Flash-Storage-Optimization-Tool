# src/performance_optimization/caching.py

import logging
import threading
import time
from collections import OrderedDict, defaultdict
from enum import Enum, auto


class EvictionPolicy(Enum):
    """Available cache eviction policies"""

    LRU = auto()  # Least Recently Used
    LFU = auto()  # Least Frequently Used
    FIFO = auto()  # First In First Out
    TTL = auto()  # Time To Live


class CachingSystem:
    """
    Advanced caching system with multiple eviction policies, statistics, and thread safety.

    Features:
    - Multiple eviction policies (LRU, LFU, FIFO, TTL)
    - Time-based expiration
    - Detailed cache statistics
    - Thread-safe operations
    - Optional callbacks for eviction events
    - Size-based and count-based limits
    """

    def __init__(self, capacity=1024, policy=EvictionPolicy.LRU, ttl=None, max_size_bytes=None, thread_safe=True, on_evict=None):
        """
        Initialize the caching system.

        Args:
            capacity (int): Maximum number of items to store in the cache
            policy (EvictionPolicy): Cache eviction policy
            ttl (int, optional): Default Time-To-Live in seconds for cache entries
            max_size_bytes (int, optional): Maximum cache size in bytes
            thread_safe (bool): Whether to make operations thread-safe
            on_evict (callable, optional): Callback function called when items are evicted
        """
        # Extract capacity value if a Config object is provided
        if hasattr(capacity, "get"):
            self.capacity = capacity.get("caching", {}).get("capacity", 1024)
        else:
            self.capacity = capacity

        # Set up policy
        if isinstance(policy, str):
            try:
                self.policy = EvictionPolicy[policy.upper()]
            except KeyError:
                raise ValueError(f"Unknown eviction policy: {policy}")
        else:
            self.policy = policy

        self.ttl = ttl
        self.max_size_bytes = max_size_bytes
        self.thread_safe = thread_safe
        self.on_evict = on_evict

        # Main cache storage
        self.cache = OrderedDict()

        # Additional data structures based on policy
        self.access_count = defaultdict(int)  # For LFU
        self.insert_time = {}  # For FIFO and TTL
        self.expire_time = {}  # For TTL
        self.size_bytes = {}  # For tracking entry sizes

        # Statistics
        self.stats = {"hits": 0, "misses": 0, "evictions": 0, "expirations": 0, "total_size_bytes": 0}

        # Thread safety
        if thread_safe:
            self.lock = threading.RLock()
        else:
            # Use a dummy context manager when thread safety is not needed
            class DummyLock:
                def __enter__(self):
                    pass

                def __exit__(self, *args):
                    pass

            self.lock = DummyLock()

    def get(self, key, default=None):
        """
        Retrieve an item from the cache.

        Args:
            key: The cache key
            default: Value to return if key is not found

        Returns:
            The cached value or default if not found
        """
        with self.lock:
            # Check if key exists and handle expiration
            if key in self.cache:
                # Check for expired entry
                if self._is_expired(key):
                    self._remove_item(key, reason="expired")
                    self.stats["misses"] += 1
                    return default

                # Item found and not expired
                self.stats["hits"] += 1

                # Update metadata based on policy
                if self.policy == EvictionPolicy.LRU:
                    self.cache.move_to_end(key)
                elif self.policy == EvictionPolicy.LFU:
                    self.access_count[key] += 1

                return self.cache[key]
            else:
                # Item not found
                self.stats["misses"] += 1
                return default

    def put(self, key, value, ttl=None):
        """
        Add or update an item in the cache.

        Args:
            key: The cache key
            value: The value to cache
            ttl (int, optional): Time-To-Live in seconds for this specific entry
        """
        with self.lock:
            # Calculate size if we're tracking bytes
            size_bytes = self._calculate_size(value) if self.max_size_bytes else 0

            # If key already exists, update it and handle size tracking
            if key in self.cache:
                old_size = self.size_bytes.get(key, 0)
                self.stats["total_size_bytes"] = self.stats["total_size_bytes"] - old_size + size_bytes

                if self.policy == EvictionPolicy.LRU:
                    self.cache.move_to_end(key)
            else:
                # Check if we need to evict based on capacity or size
                self._ensure_capacity(size_bytes)

                # Add size to total if tracking
                if self.max_size_bytes:
                    self.stats["total_size_bytes"] += size_bytes

            # Update the cache and metadata
            self.cache[key] = value

            if self.policy == EvictionPolicy.LFU:
                self.access_count[key] = 1

            now = time.time()
            self.insert_time[key] = now

            # Handle TTL
            if ttl is not None or self.ttl is not None:
                expiration = now + (ttl if ttl is not None else self.ttl)
                self.expire_time[key] = expiration

            # Track size if needed
            if self.max_size_bytes:
                self.size_bytes[key] = size_bytes

    def invalidate(self, key):
        """
        Remove an item from the cache.

        Args:
            key: The key to remove
        """
        with self.lock:
            if key in self.cache:
                self._remove_item(key, reason="invalidated")

    def clear(self):
        """Clear the entire cache."""
        with self.lock:
            self.cache.clear()
            self.access_count.clear()
            self.insert_time.clear()
            self.expire_time.clear()
            self.size_bytes.clear()
            self.stats["total_size_bytes"] = 0

    def get_hit_ratio(self):
        """
        Calculate the cache hit ratio.

        Returns:
            float: The ratio of cache hits to total accesses, or 0 if no accesses
        """
        with self.lock:
            total = self.stats["hits"] + self.stats["misses"]
            if total == 0:
                return 0.0
            return self.stats["hits"] / total

    def get_stats(self):
        """
        Get cache statistics.

        Returns:
            dict: Dictionary with cache statistics
        """
        with self.lock:
            stats = self.stats.copy()
            stats["current_size"] = len(self.cache)
            stats["hit_ratio"] = self.get_hit_ratio()
            return stats

    def get_keys(self):
        """
        Get all cache keys.

        Returns:
            list: List of all keys in the cache
        """
        with self.lock:
            return list(self.cache.keys())

    def touch(self, key):
        """
        Update the access time for a key without retrieving its value.
        Useful for keeping items in LRU cache without reading them.

        Args:
            key: The key to touch

        Returns:
            bool: True if key exists and was touched, False otherwise
        """
        with self.lock:
            if key in self.cache:
                if self.policy == EvictionPolicy.LRU:
                    self.cache.move_to_end(key)
                elif self.policy == EvictionPolicy.LFU:
                    self.access_count[key] += 1
                return True
            return False

    def set_ttl(self, key, ttl):
        """
        Set or update the TTL for a specific key.

        Args:
            key: The cache key
            ttl (int): New Time-To-Live in seconds

        Returns:
            bool: True if key exists and TTL was set, False otherwise
        """
        with self.lock:
            if key in self.cache:
                self.expire_time[key] = time.time() + ttl
                return True
            return False

    def contains(self, key):
        """
        Check if key exists in cache and is not expired.

        Args:
            key: The key to check

        Returns:
            bool: True if key exists and is not expired
        """
        with self.lock:
            if key in self.cache:
                if self._is_expired(key):
                    self._remove_item(key, reason="expired")
                    return False
                return True
            return False

    def _is_expired(self, key):
        """Check if a cache entry is expired."""
        if key in self.expire_time:
            now = time.time()
            return now > self.expire_time[key]
        return False

    def _calculate_size(self, value):
        """Calculate the size of a value in bytes."""
        # This is a simplistic implementation
        # For more accurate size calculation, you might want to use
        # sys.getsizeof or a more sophisticated approach
        if isinstance(value, (bytes, bytearray)):
            return len(value)
        elif isinstance(value, str):
            return len(value.encode("utf-8"))
        else:
            # Approximate size for other objects
            try:
                import sys

                return sys.getsizeof(value)
            except:
                return 100  # Default size if we can't determine

    def _ensure_capacity(self, new_item_size=0):
        """
        Ensure there's enough capacity for a new item by evicting old items if necessary.

        Args:
            new_item_size (int): Size of new item in bytes (if tracking sizes)
        """
        # Check capacity limit
        while len(self.cache) >= self.capacity and self.cache:
            self._evict_one()

        # Check size limit if we're tracking bytes
        if self.max_size_bytes:
            while (self.stats["total_size_bytes"] + new_item_size > self.max_size_bytes) and self.cache:
                self._evict_one()

    def _evict_one(self):
        """Evict one item based on the current policy."""
        if not self.cache:
            return

        key_to_evict = None

        if self.policy == EvictionPolicy.LRU:
            # In OrderedDict, the first item is the oldest
            key_to_evict, _ = self.cache.popitem(last=False)

        elif self.policy == EvictionPolicy.FIFO:
            # Find the oldest item by insertion time
            key_to_evict = min(self.insert_time, key=lambda k: self.insert_time[k])
            del self.cache[key_to_evict]

        elif self.policy == EvictionPolicy.LFU:
            # Find the least frequently used item
            if self.access_count:
                key_to_evict = min(self.access_count, key=lambda k: self.access_count[k])
                del self.cache[key_to_evict]
                del self.access_count[key_to_evict]

        # For any policy, if a key was selected, clean up metadata
        if key_to_evict:
            self._cleanup_metadata(key_to_evict)
            self.stats["evictions"] += 1

            # Call eviction callback if provided
            if self.on_evict:
                try:
                    self.on_evict(key_to_evict)
                except Exception as e:
                    logging.error(f"Error in eviction callback: {e}")

    def _remove_item(self, key, reason="removed"):
        """Remove an item and update statistics."""
        if key in self.cache:
            value = self.cache[key]
            del self.cache[key]
            self._cleanup_metadata(key)

            if reason == "expired":
                self.stats["expirations"] += 1

            # Call eviction callback if provided
            if self.on_evict:
                try:
                    self.on_evict(key)
                except Exception as e:
                    logging.error(f"Error in eviction callback: {e}")

            return value
        return None

    def _cleanup_metadata(self, key):
        """Clean up metadata for a key that's being removed."""
        if key in self.access_count:
            del self.access_count[key]

        if key in self.insert_time:
            del self.insert_time[key]

        if key in self.expire_time:
            del self.expire_time[key]

        if key in self.size_bytes:
            self.stats["total_size_bytes"] -= self.size_bytes[key]
            del self.size_bytes[key]
