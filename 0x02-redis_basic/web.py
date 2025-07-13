#!/usr/bin/env python3
"""
This module implements a simple web cache and URL access counter using Redis.
"""

import redis
import requests
from typing import Callable
from functools import wraps

# Initialize Redis connection
redis_client = redis.Redis()


def count_and_cache(method: Callable) -> Callable:
    """
    Decorator to track access count and cache HTML content for 10 seconds.
    """

    @wraps(method)
    def wrapper(url: str) -> str:
        # Increment the access counter for the URL
        redis_client.incr(f"count:{url}")

        # Try to get cached page
        cached = redis_client.get(f"url:{url}")
        if cached:
            return cached.decode('utf-8')

        # Fetch, cache and return the page
        result = method(url)
        redis_client.setex(f"url:{url}", 10, result)  # setex = set + expire
        return result

    return wrapper


@count_and_cache
def get_page(url: str) -> str:
    """
    Fetches the HTML content of a given URL and returns it.

    Args:
        url (str): The URL to fetch.

    Returns:
        str: The HTML content of the page.
    """
    response = requests.get(url)
    return response.text
