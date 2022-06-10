import asyncio

async def async_wait(f, *args, **kwargs):
    return await asyncio.get_event_loop().run_in_executor(None, lambda: f(*args, **kwargs))