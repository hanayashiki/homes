from typing import *
import logging

import asyncio
import asyncio.base_events

import websockets
from websockets.protocol import WebSocketCommonProtocol
from homes.redirector import Redirector, InvalidState
from homes.protocol import TCPMessage, get_connection_id, BEGIN, MID, END
import ssl
import socket
import time

logger = logging.getLogger("homes")

class Client(Redirector):

  """
  Local <--[TCP local]--> client <--[Ws client]--> Server ...
  """

  def __init__(self,
               client_local_addr: Tuple[str, int],
               server_client_addr: Tuple[str, int],
               ssl_context: ssl.SSLContext=None,
               token: str="",
               force_ipv4: bool=True,
               max_connections: int=100):
    self.client_local_addr = client_local_addr
    self.client_local_ip, self.client_local_port = self.client_local_addr
    self.server_client_addr = server_client_addr
    self.server_client_ip, self.server_client_port = self.server_client_addr
    self.ssl_context = ssl_context
    self.token = token
    self.max_connections = max_connections
    self.socket_family = socket.AF_INET if force_ipv4 else None

    self.client_connections: Dict[int, Tuple[asyncio.StreamReader, asyncio.StreamWriter]] = {}

    super().__init__(ws=None)

  async def establish_server_connection(self, message_id: int):

    if len(self.client_connections) > self.max_connections:
      await self.ws.send(TCPMessage(id=message_id, tag=END, data=b''))
      return

    if message_id in self.client_connections:
      reader, writer = self.client_connections[message_id]
      writer.close()

    logger.debug(f"{hex(message_id)} Connection started")
    reader, writer = await asyncio.open_connection(host=self.client_local_ip,
                                                   port=self.client_local_port,
                                                   family=self.socket_family)
    logger.debug(f"{hex(message_id)} Connection open")
    self.client_connections[message_id] = (reader, writer)

    asyncio.ensure_future(self.forward_client_msg(message_id, reader))

  async def forward_server_msg(self):
    try:
      while self.ws and not self.ws.closed:
        message = await self.ws.recv()
        tcp_message: TCPMessage = TCPMessage.from_bytes(message)

        if tcp_message.tag != BEGIN and tcp_message.id not in self.client_connections:
          logger.warning(f"Unknown id: {hex(tcp_message.id)}")
          continue

        logger.debug(f"{hex(tcp_message.id)} {tcp_message.tag} Receive message {len(tcp_message.data)}")
        try:
          if tcp_message.tag == BEGIN:
            await self.establish_server_connection(message_id=tcp_message.id)
        except ConnectionRefusedError:
          logger.error(f"Connection to {self.client_local_addr} is refused. ")
          await self.ws.send(TCPMessage(id=tcp_message.id, tag=END, data=b'').to_bytes())
          continue
        reader, writer = self.client_connections[tcp_message.id]
        writer.write(tcp_message.data)
        await writer.drain()
        logger.debug(f"{hex(tcp_message.id)} {tcp_message.tag} Send message {len(tcp_message.data)}")

        if tcp_message.tag == END:
          writer.close()
          if tcp_message.id in self.client_connections:
            del self.client_connections[tcp_message.id]
    finally:
      pass

  async def forward_client_msg(self, id: int, reader: asyncio.StreamReader):
    try:
      seq = 0
      while id in self.client_connections and not reader.at_eof():
        data: bytes = await reader.read(4096)
        if seq == 0:
          tag = BEGIN
        else:
          tag = MID

        if tag == BEGIN or len(data) > 0:
          await self.ws.send(TCPMessage(id=id, tag=tag, data=data).to_bytes())
          logger.debug(f"Send message {len(data)}")

        seq += 1

      await self.ws.send(TCPMessage(id=id, tag=END, data=b'').to_bytes())
      logger.debug(f"Send message {0}")
    finally:
      pass

  async def run(self):
    if self.ssl_context:
      proto = "wss"
    else:
      proto = "ws"
    uri = f"{proto}://{self.server_client_ip}:{self.server_client_port}/{self.token}"

    while True:
      try:
        async with websockets.connect(uri,
                                      ssl=self.ssl_context) as ws:
          self.ws = ws
          logger.info(f"Connected to {uri}")
          await self.forward_server_msg()
      except InvalidState as e:
        time.sleep(0.5)
        logger.error(f"Connection incorrect, reconnecting: {e}")
      except websockets.exceptions.ConnectionClosed as e:
        time.sleep(5)
        logger.error(f"Connection closed, reconnecting: {e}")
      except Exception as e:
        time.sleep(5)
        logger.error(f"Something else happened: {e}")
      finally:
        self.client_connections.clear()


