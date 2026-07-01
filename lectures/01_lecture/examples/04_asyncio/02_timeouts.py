import asyncio


async def eternity() -> None:
    await asyncio.sleep(3600)  # 1 hour sleep
    print("yay!")


async def main():
    try:
        await asyncio.wait_for(eternity(), timeout=1)  # wait for at most 1 second
    except TimeoutError:
        print("timeout!")


asyncio.run(main())
