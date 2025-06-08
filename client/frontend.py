import rich
import asyncio
from aioconsole import ainput as input
import client

async def main():
    client_task = asyncio.create_task(client.main_client())
    input_task = asyncio.create_task(front())

    await asyncio.gather(client_task, input_task)


async def front():
    while True:
        try:
            await input("> ")
        except Exception:
            break

if __name__ == "__main__":
    asyncio.run(main())

