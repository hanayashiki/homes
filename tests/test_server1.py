from homes.server_core import Server
from homes.client_core import Client
import threading
import asyncio
import socket
import time
import logging

logger = logging.getLogger("homes")
logging.basicConfig(format='%(asctime)s %(filename)16s %(funcName)32s : %(levelname)s  %(message)s')
logger.setLevel(logging.DEBUG)

text = '我是你妈'.encode('utf-8')

def send_text(t, addr):
  time.sleep(2)
  sock = socket.socket()
  sock.connect(addr)
  sock.send(t)
  logger.info(f"text sent: {t}")
  data = sock.recv(4096)
  logger.info(f"text recv: {data}")
  assert data == t

async def handle_echo(reader, writer):
  data = await reader.read(100)
  message = data.decode()
  addr = writer.get_extra_info('peername')

  logger.info(f"Received {message!r} from {addr!r}")

  logger.info(f"Send: {message!r}")
  writer.write(data)
  await writer.drain()

  logger.info("Close the connection")
  writer.close()

async def local():
  server = await asyncio.start_server(
    handle_echo, 'localhost', 1234)

  addr = server.sockets[0].getsockname()
  logger.info(f'Serving on {addr}')

  async with server:
    await server.serve_forever()

def start_local():
  asyncio.run(local())

def start_server(client_port, server_port, **args):
  server = Server(server_client_addr=('localhost', client_port),
                  server_remote_addr=('localhost', server_port),
                  **args)
  asyncio.run(server.run())

def start_client(client_port):
  client = Client(server_client_addr=('localhost', client_port),
                  client_local_addr=('localhost', 1234))
  asyncio.run(client.run())


def test_server():
  t1 = threading.Thread(target=start_server, args=(11451, 45141,))
  t1.start()

  t3 = threading.Thread(target=start_local, args=())
  t3.start()

  t4 = threading.Thread(target=start_client, args=(11451,))
  t4.start()

  t2 = threading.Thread(target=send_text, args=(text, ('localhost', 45141)))
  t2.start()

  t5 = threading.Thread(target=send_text, args=("草泥马".encode("utf-8"), ('localhost', 45141)))
  t5.start()

test_server()