#!/usr/bin/env python3
""" Main file to test get_page caching """

from web import get_page, redis_client

url = "http://slowwly.robertomurray.co.uk/delay/2000/url/http://example.com"

html = get_page(url)
print(html[:200])  # Print first 200 characters of HTML

print(f"URL accessed {redis_client.get(f'count:{url}').decode()} times")
