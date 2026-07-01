import asyncio


async def factorial(name: str, number: int) -> None:
    result = 1
    for i in range(2, number + 1):
        if number == 2:
            raise RuntimeError("Whoops 2!")
        if number == 3:
            raise ValueError("Whoops 3!")
        print(f"Task {name}: Compute factorial({i})...")
        await asyncio.sleep(1)
        result *= i
    print(f"Task {name}: factorial({number}) = {result}")
    return result


async def main():
    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(factorial("A", 2))
            tg.create_task(factorial("B", 3))
            tg.create_task(factorial("C", 4))
            print("tasks pending to start")
    except* (ValueError, RuntimeError) as excgroup:
        # * in except mostly important for coroutines! Before that, we have to catch all exceptions by hand!
        for exc in excgroup.exceptions:
            print(f"Caught exception: {exc} with class {exc.__class__.__name__}")

    print("tasks complete")


asyncio.run(main())
