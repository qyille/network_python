import asyncio


async def factorial(number: int) -> tuple[int, int]:
    result = 1
    for i in range(2, number + 1):
        await asyncio.sleep(1)
        result *= i
    return number, result


async def main():
    for _, future in enumerate(
        asyncio.as_completed([factorial(4), factorial(3), factorial(5), factorial(2)])
    ):
        number, result = await future
        print(f"Factorial({number}) = {result}")


asyncio.run(main())
