"""
Concepts: OOP + Decorators + Async
Run: python api_fetcher_fixed.py
"""

import asyncio
import functools
import time
from typing import Any, Dict, Optional

import httpx

# -----------------------
# Decorators (safe version)
# -----------------------



def log_calls(func):
  #   """Prints function name and key args before and after call."""
  @functools.wraps(func)
  def sync_wrapper(*args,**kwargs):
    print(f"{func.__name__}called with args={args[1:]},kwargs={kwargs}")
    result=func(*args,**kwargs)
    print(f"{func.__name__}retuned type={type(result).__name__}")
    return result
  
  @functools.wraps(func)
  async def async_wrapper(*args, **kwargs):
        print(f"  {func.__name__} called with args={args[1:]}, kwargs={kwargs}")
        result = await func(*args, **kwargs)
        print(f" {func.__name__} returned type={type(result).__name__}")
        return result
  
  # Supporting both sync and async

  return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper



def timed(func):
  #  Measures execution time

  @functools.wraps(func)
  def sync_wrapper(*args,**kwargs):
    start=time.perf_counter()
    try:
        return func(*args,**kwargs)
    finally:
        elapsed=(time.perf_counter()-start)*1000
        print(f"{func.__name__} took {elapsed:.2f} ms")


  @functools.wraps(func)
  async def async_wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            return await func(*args, **kwargs)
        finally:
            elapsed = (time.perf_counter() - start) * 1000
            print(f"⏱  {func.__name__} took {elapsed:.2f} ms")

  return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper


def retry_async_safe(retries: int = 3, delay: float = 0.5, backoff: float = 2.0):
    """Retries an async function upon failure."""
    def _decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            _delay = delay
            last_err = None
            for attempt in range(1, retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_err = e
                    print(f"⚠️ {func.__name__} failed (attempt {attempt}/{retries}): {e}")
                    if attempt < retries:
                        await asyncio.sleep(_delay)
                        _delay *= backoff
            raise last_err
        return wrapper
    return _decorator

#  Agar API call fail hota hai toh ye automatic retry karega.
# -----------------------
# OOP API Client
# -----------------------
class APIClient:
    """
    Async HTTP client with base_url & timeout.
    Use like: async with APIClient("https://example.com") as c: ...
    """

    def __init__(self, base_url: str, timeout: float = 10.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout)
        return self
    
    # create a single AsyncClient per context
     #     Jab tum context enter karti ho (async with), tab ek httpx.AsyncClient object create hota hai.
# Ye client ek open HTTP session maintain karega, jisse tum multiple requests efficiently bhej sakti ho.




    async def __aexit__(self, exc_type, exc, tb):
        if self._client:
            await self._client.aclose()
            self._client = None
# Ye method context manager ke exit hone par (i.e., async with block khatam hone par) call hota hai.
# Parameters:
# exec_type: Exception ka type (agar aaya ho).
# exc: Exception ka actual object.
# tb: Traceback (error ka stack trace).





    @retry_async_safe(retries=3, delay=0.3)
    @timed
    @log_calls
    async def get_json(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if self._client is None:
            raise RuntimeError("APIClient not initialized. Use 'async with APIClient(...) as c:'")
        resp = await self._client.get(path, params=params)
        resp.raise_for_status()
        return resp.json()

# -----------------------
# Orchestration
# -----------------------
@timed
async def fetch_demo():
    async with APIClient("https://jsonplaceholder.typicode.com") as jp:
        users_task = jp.get_json("/users/1")
        post_task = jp.get_json("/posts/1")
        comments_task = jp.get_json("/comments", params={"postId": 1})

        async with APIClient("https://httpbin.org") as hb:
            slow1 = hb.get_json("/delay/1")  # ~1s
            slow2 = hb.get_json("/delay/2")  # ~2s

            users, post, comments, d1, d2 = await asyncio.gather(
                users_task, post_task, comments_task, slow1, slow2
            )

    print("\n📦 Summary")
    print(f"- User: {users.get('name')} | Email: {users.get('email')}") ##User ka name aur email print karega.
    print(f"- Post: {post.get('title')[:60]!r} (id={post.get('id')})") ##Post ka title (sirf pehle 60 characters) aur ID print karega.
    print(f"- Comments fetched: {len(comments)}")# #Total comments count print karega.
    print(f"- Delayed calls ok: delay1 keys={list(d1.keys())[:3]}, delay2 keys={list(d2.keys())[:3]}\n")

    # #Delay wale responses ke first 3 keys print karega (check karne ke liye ki data aaya hai).


def main():
    print(" Starting Async API Fetcher (Fixed)\n")
    asyncio.run(fetch_demo())
    print("Done")

if __name__ == "__main__":
    main()
