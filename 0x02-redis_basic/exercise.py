#!/usr/bin/env python3
"""
This module provides a Cache class that interfaces with a Redis database.
It supports storing data, retrieving with type conversion, call counting,
call history logging, and more using Redis.
"""

import redis
import uuid
import functools
from typing import Union, Callable, Optional


def count_calls(method: Callable) -> Callable:
    """
    Decorator that counts how many times a method is called.
    Stores the count in Redis using the method's qualified name.
    """
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        """Increments call count each time the method is called."""
        self._redis.incr(method.__qualname__)
        return method(self, *args, **kwargs)
    return wrapper


def call_history(method: Callable) -> Callable:
    """
    Decorator that stores the history of inputs and outputs for a method.
    Inputs are stored under <method>:inputs and outputs under <method>:outputs.
    """
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        """Logs input arguments and output result to Redis lists."""
        input_key = method.__qualname__ + ":inputs"
        output_key = method.__qualname__ + ":outputs"

        self._redis.rpush(input_key, str(args))
        result = method(self, *args, **kwargs)
        self._redis.rpush(output_key, str(result))
        return result
    return wrapper


def replay(method: Callable):
    """
    Displays the history of calls of a particular function.
    It prints the number of calls, inputs, and corresponding outputs.
    """
    redis_instance = redis.Redis()
    qualname = method.__qualname__
    inputs = redis_instance.lrange(f"{qualname}:inputs", 0, -1)
    outputs = redis_instance.lrange(f"{qualname}:outputs", 0, -1)
    count = redis_instance.get(qualname)
    print(f"{qualname} was called {int(count or 0)} times:")

    for inp, out in zip(inputs, outputs):
        print(f"{qualname}(*{inp.decode('utf-8')}) -> {out.decode('utf-8')}")


class Cache:
    """
    The Cache class provides methods to store and retrieve data from Redis.
    It tracks how often methods are called and logs inputs/outputs for replay.
    """

    def __init__(self):
        """
        Initializes the Redis client and flushes the database.
        """
        self._redis = redis.Redis()
        self._redis.flushdb()

    @call_history
    @count_calls
    def store(self, data: Union[str, bytes, int, float]) -> str:
        """
        Stores the given data in Redis using a randomly generated UUID key.

        Args:
            data: The data to store (str, bytes, int, or float).

        Returns:
            str: The key under which the data is stored.
        """
        key = str(uuid.uuid4())
        self._redis.set(key, data)
        return key

    def get(self, key: str, fn: Optional[Callable] = None) -> Union[str, bytes, int, float, None]:
        """
        Retrieves data from Redis using the given key. Optionally applies a conversion function.

        Args:
            key (str): The key to retrieve data from.
            fn (Callable, optional): A function to apply to the retrieved data.

        Returns:
            The retrieved data, possibly transformed by fn. Returns None if key does not exist.
        """
        value = self._redis.get(key)
        if value is None:
            return None
        return fn(value) if fn else value

    def get_str(self, key: str) -> Optional[str]:
        """
        Retrieves a UTF-8 string from Redis using the given key.

        Args:
            key (str): The key to retrieve.

        Returns:
            Optional[str]: Decoded string or None.
        """
        return self.get(key, fn=lambda d: d.decode('utf-8'))

    def get_int(self, key: str) -> Optional[int]:
        """
        Retrieves an integer from Redis using the given key.

        Args:
            key (str): The key to retrieve.

        Returns:
            Optional[int]: Integer value or None.
        """
        return self.get(key, fn=int)
