import asyncio
import time


async def another_eternity() -> None:
    try:
        await asyncio.sleep(3600)
        print(f"{time.strftime('%X')} yay!")
    except asyncio.CancelledError:
        print(f"{time.strftime('%X')} Hey, I am cancelled!")
        raise
    finally:
        await asyncio.sleep(3)  # 30
        print(f"{time.strftime('%X')} coro finished")


async def main():
    print(f"{time.strftime('%X')} started")

    try:
        # Send CancelledError to coro after 1 sec and wait for coro completion
        await asyncio.wait_for(another_eternity(), timeout=1)
    except asyncio.TimeoutError:
        print(f"{time.strftime('%X')} timeout!")

    print(f"{time.strftime('%X')} block finished")


asyncio.run(main())
