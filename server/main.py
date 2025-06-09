import asyncio
import ssl
import re
from rich import print

"""
    Callback function to handle a single client connection.
    `reader` is an asyncio.StreamReader for reading data.
    `writer` is an asyncio.StreamWriter for writing data.
"""
writers = set()
users = dict()
CERT_FILE = 'server.crt'
KEY_FILE = 'server.key'

async def handle_client(reader, writer):
    addr = writer.get_extra_info('peername')
    print(f"Accepted connection from {addr}")
    writers.add(writer)
    users[(addr[0], addr[1])] = "None"
    print(f"Currently connected clients: {[writer.get_extra_info('peername') for writer in writers]}")
    try:
        while True:
            # Read data from the client
            data = await reader.read(1024) # Read up to 1024 bytes
            if not data:
                # Client disconnected
                print(f"Client {addr} disconnected.")
                break

            message = data.decode().strip()
            print(f"Received from {addr}: {message!r}")
            recv_nick = re.search("^/nick", message)
            if (recv_nick):
                nick = message[recv_nick.end():]
                users[(addr[0], addr[1])] = nick.strip()

            currently_online_clients = f"{len(list(writers)):03}".encode()
            broadcast_message = f"[{users[(addr[0], addr[1])]}] {message}".encode()
            send_tasks = []

            for client_writer in list(writers):
                try:
                    client_writer.write(currently_online_clients)
                    await client_writer.drain()
                    client_writer.write(broadcast_message)
                    send_tasks.append(client_writer.drain())
                except Exception as e:
                    print(f"Error sending to client {client_writer.get_extra_info('peername')}: {e}")
                    # TODO remove client_writer here if error signalizes more significant error

            if send_tasks:
                await asyncio.gather(*send_tasks, return_exceptions=True)



    except asyncio.CancelledError:
        print(f"Connection with {addr} cancelled.")
    except Exception as e:
        print(f"Error handling client {addr}: {e}")
    finally:
        print(f"Closing connection with {addr}")
        
        try:
            writers.remove(writer)
        except ValueError:
            pass

        writer.close()
        await writer.wait_closed() # Ensure the writer is truly closed
    

async def main():
    host = "0.0.0.0"
    port = 8080

    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    try:
        ssl_context.load_cert_chain(CERT_FILE, KEY_FILE)
    except FileNotFoundError:
        print(f"Error: Certificate file '{CERT_FILE}' or key file '{KEY_FILE}' not found.")
        print("Please generate them using: ")
        print("  openssl genrsa -out server.key 2048")
        print("  openssl req -new -x509 -key server.key -out server.crt -days 365")
        return
    except ssl.SSLError as e:
        print(f"Error loading SSL certificate/key: {e}")
        print("Ensure the key is not password-protected or provide a password.")
        return

    server = await asyncio.start_server(
            handle_client, host, port
            )

    addrs = ", ".join(str(sock.getsockname()) for sock in server.sockets)
    print(f"Serving on {addrs}")

    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Server stopped by user.")

