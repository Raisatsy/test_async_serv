import asyncio
import random
import datetime
from asyncio import StreamReader, StreamWriter

SERVER_HOST: str = "localhost"
SERVER_PORT: int = 8888
LOG_FILE: str = "server.log"


class Server:
    def __init__(self) -> None:
        self.clients = []
        self.response_number: int = 0
        self.log_queue: asyncio.Queue = asyncio.Queue()
        self.current_data: str = datetime.datetime.now().strftime("%Y-%m-%d")

    async def handle_client(self, reader: StreamReader, writer: StreamWriter) -> None:
        self.clients.append(writer)
        client_id: int = len(self.clients)

        while True:
            data: bytes = await reader.readline()
            if not data:
                break
            time_to_request: str = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]

            request_text: str = data.decode().strip()

            if random.random() <= 0.1:
                log_entry: str = self.log_response(time_to_request, request_text, "", "", ignored=True)
                self.log_queue.put_nowait(log_entry)
                continue

            await asyncio.sleep(random.uniform(0.1, 1.0))

            response_text: str = f"[{self.response_number}] PONG ({client_id})"

            response: bytes = f"{response_text}\n".encode()
            writer.write(response)
            await writer.drain()

            time_to_response = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]

            log_entry: str = self.log_response(time_to_request, request_text, response_text, time_to_response)
            self.log_queue.put_nowait(log_entry)

            self.response_number += 1

        writer.close()

    def log_response(self, time_to_request: str, request_text: str, response_text: str, time_to_response: str,
                     ignored: bool = False) -> str:
        if ignored:
            log_entry = f"{self.current_data};{time_to_request};{request_text};(проигнорировано);(проигнорировано);"
        else:
            log_entry = f"{self.current_data};{time_to_request};{request_text};{self.current_data};{time_to_response};{response_text}"

        return log_entry

    async def log_to_file(self) -> None:
        while True:
            log_entry: str = await self.log_queue.get()
            with open(LOG_FILE, 'a') as f:
                f.write(log_entry + "\n")

    async def send_keepalive(self) -> None:
        while True:
            await asyncio.sleep(5)

            for client in self.clients:
                keepalive = f"[{self.response_number}] keepalive\n"
                client.write(keepalive.encode())
                await client.drain()
                self.response_number += 1

    async def start(self) -> None:
        server = await asyncio.start_server(
            self.handle_client, SERVER_HOST, SERVER_PORT
        )

        asyncio.create_task(self.send_keepalive())
        asyncio.create_task(self.log_to_file())

        async with server:
            await server.serve_forever()


async def main():
    server: Server = Server()
    await server.start()


if __name__ == "__main__":
    asyncio.run(main())
