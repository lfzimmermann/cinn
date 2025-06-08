import asyncio
import typing
from aioconsole import ainput as input # For async input
from rich import print
from os import system
from sys import argv


CURRENT_USERS = 0
SEND_MSG_BUFFER = []
RECV_MSG_BUFFER = []
PRINT_MSG_BUFFER = []
PRINT_MSG_BUFFER_SIZE = 10

async def handle_input():
    msg = await input("")
    SEND_MSG_BUFFER.append(msg)

async def handle_printing() -> int:
    global RECV_MSG_BUFFER # If you modify this list (pop), declare it global
    global PRINT_MSG_BUFFER # <--- DECLARE IT GLOBAL HERE!
    global PRINT_MSG_BUFFER_SIZE # Declare if modified within the function
    global CURRENT_USERS
    try:
        for _ in range(len(RECV_MSG_BUFFER)):
            PRINT_MSG_BUFFER.append(RECV_MSG_BUFFER.pop(0))

        print(f"{CURRENT_USERS} active users")
        for msg in PRINT_MSG_BUFFER:
            print(msg)
        print("$> ", end='')
        return 1
    except Exception as e:
        print(f"Printing of RECV_MSG_BUFFER elements failed with: {e!r}")
        return -1
            

async def handle_receiving(reader: asyncio.StreamReader):
    global CURRENT_USERS
    while True:
        try:
            data = await reader.read(256)
            if not data:
                print("Connection closed.")
                return

            msg = data.decode()
            CURRENT_USERS = int(msg[:3])
            RECV_MSG_BUFFER.append(msg[3:])

            system("clear")
            await handle_printing()
        except Exception as e:
            print(f"Receiving from server failed with: {e!r}")
            break


async def handle_sending(writer: asyncio.StreamWriter):
    print("$> ", end='')
    while True:
        await handle_input()
        for _ in range(len(SEND_MSG_BUFFER)):
            msg = SEND_MSG_BUFFER.pop(0)
            data = msg.encode()
            try:
                # print(f"Sending {msg!r} to server.")
                writer.write(data)
                await writer.drain()
            except Exception as e:
                print(f"Sending data failed with: {e!r}")
                break

async def main_client():
    print("Welcome to [bold magenta]chatpy[/bold magenta]!")
    
    try:
        host = argv[1]
        port = int(argv[2])
    except IndexError:
        print("Usage: python client.py <HOST> <PORT>")
        exit(1)
    except ValueError:
        print("Error: PORT must be an integer.")
        exit(1)

    reader, writer = await asyncio.open_connection(host, port)

    try:
        recv = asyncio.create_task(handle_receiving(reader))
        send = asyncio.create_task(handle_sending(writer))

        await asyncio.gather(recv, send)
    except RuntimeError as e:
        print(f"There is no running loop in current thread: {e!r}")
    finally:
        writer.close()
        await writer.wait_closed()




if __name__ == "__main__":
    try:
        asyncio.run(main_client())
    except KeyboardInterrupt:
        print("\nClient closed by user.")
