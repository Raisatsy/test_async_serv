import asyncio
import random
import datetime
from asyncio import StreamReader, StreamWriter
from typing import Tuple


class Client:
    def __init__(self, client_id: int):
        self.client_id: int = client_id
        self.request_number: int = 0
        self.response_queue: asyncio.Queue = asyncio.Queue()
        self.current_data: str = datetime.datetime.now().strftime("%Y-%m-%d")

    async def send_ping(self, reader: StreamReader, writer: StreamWriter):
        while True:
            await asyncio.sleep(random.uniform(0.3, 3.0))

            request_text: str = f"[{self.request_number}] PING"

            request: bytes = f"{request_text}\n".encode()
            writer.write(request)
            await writer.drain()
            time_to_request: str = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]

            try:
                response: bytes = await asyncio.wait_for(reader.readline(), timeout=1.0)
                response_text: str = response.decode().strip()

                time_to_response: str = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]

                if "keepalive" in response_text:
                    additional_response: bytes = await asyncio.wait_for(reader.readline(), timeout=1.0)
                    additional_response_text: str = additional_response.decode().strip()
                    self.response_queue.put_nowait(
                        (time_to_request, request_text, additional_response_text, time_to_response))

                self.response_queue.put_nowait((time_to_request, request_text, response_text, time_to_response))

                self.request_number += 1

            except asyncio.TimeoutError:
                response_text: str = "(таймаут)"
                time_to_response: str = ""

                self.response_queue.put_nowait((time_to_request, request_text, response_text, time_to_response))

                self.request_number += 1

    def log_request(self, time_to_request: str, request_text: str, response_text: str, time_to_response: str) -> None:
        if "keepalive" in response_text:
            log_entry: str = f"{self.current_data};{time_to_response};{response_text}"
        else:
            log_entry: str = f"{self.current_data};{time_to_request};{request_text};{time_to_response};{response_text}"
        log_file: str = f"client{self.client_id}.log"
        with open(log_file, "a") as f:
            f.write(log_entry + "\n")

    async def start(self) -> None:
        await asyncio.sleep(0.5)
        reader, writer = await asyncio.open_connection("localhost", 8888)

        asyncio.create_task(self.send_ping(reader, writer))

        while True:
            response: Tuple[str, str, str, str] = await self.response_queue.get()
            time_to_request, request_text, response_text, time_to_response = response

            self.log_request(time_to_request, request_text, response_text, time_to_response)


async def main():
    client1: Client = Client(1)
    client1_task: asyncio.Task = asyncio.create_task(client1.start())

    client2: Client = Client(2)
    client2_task: asyncio.Task = asyncio.create_task(client2.start())
    await asyncio.gather(client1_task, client2_task)


if __name__ == "__main__":
    asyncio.run(main())
