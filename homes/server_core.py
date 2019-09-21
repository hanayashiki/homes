from typing import *
import logging

import asyncio
import asyncio.base_events

import websockets
from websockets.protocol import WebSocketCommonProtocol
from homes.redirector import Redirector
from homes.protocol import TCPMessage, get_connection_id, BEGIN, MID, END
import ssl

logger = logging.getLogger("homes")

class Server(Redirector):

  """
  ... client <--[Ws client]--> Server <--[TCP remote]--> remote
  """

  def __init__(self,
               server_client_addr: Tuple[str, int],
               server_remote_addr: Tuple[str, int],
               ssl_context: ssl.SSLContext=None,
               token: str="",
               max_connections: int=100,
               ):
    self.server_client_addr = server_client_addr
    self.server_client_ip, self.server_client_port = self.server_client_addr
    self.server_remote_addr = server_remote_addr
    self.server_remote_ip, self.server_remote_port = self.server_remote_addr
    self.ssl_context = ssl_context
    self.token = token
    self.max_connections = max_connections

    self.buffers: Dict[int, asyncio.Queue] = {}

    super().__init__(ws=None)

  async def server_client_serve(self, ws: WebSocketCommonProtocol, path: str):
    try:
      if path != f"/{self.token}":
        logger.error(f"Incorrect path: {path}")
        await ws.close()
        return
      if self.ws and not self.ws.closed:
        await self.ws.close()
      self.ws = ws
      await self.forward_client_msg()

    finally:
      if self.ws:
        self.buffers.clear()
        await self.ws.close()
      pass

  async def forward_client_msg(self):
    try:
      while self.ws and not self.ws.closed:
        try:
          data: bytes = await self.ws.recv()
          message = TCPMessage.from_bytes(data)

          if message.id not in self.buffers:
            break

          await self.buffers[message.id].put(message.data)
        except websockets.exceptions.ConnectionClosedOK:
          break
    finally:
      pass

  async def forward_buffer_msg(self, writer: asyncio.StreamWriter):
    ip, port = writer.get_extra_info('peername')
    message_id = get_connection_id((ip, port))
    try:
      while message_id in self.buffers:
        message = await self.buffers[message_id].get()

        if len(message) == 0:
          del self.buffers[message_id]
          writer.close()
          return

        writer.write(message)
        await writer.drain()
    except ConnectionResetError:
      logger.debug(f"Connection lost from {(ip, port)}")
      pass
    finally:
      pass

  async def forward_remote_msg(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    try:
      ip, port = writer.get_extra_info('peername')
      message_id = get_connection_id((ip, port))
      seq = 0
      while not reader.at_eof():
        data: bytes = await reader.read(4096)

        if seq == 0:
          tag = BEGIN
        else:
          tag = MID

        if tag == BEGIN or len(data) > 0:
          message = TCPMessage(id=message_id, tag=tag, data=data)
          await self.ws.send(message.to_bytes())

        seq += 1
      message = TCPMessage(id=message_id, tag=END, data=b'')
      await self.ws.send(message.to_bytes())
    finally:
      pass

  async def server_remote_serve(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):

    logger.info(f"Connection from {writer.get_extra_info('peername')}")

    if not self.ws or self.ws.closed:
      logger.error(f"Client is not started. ")
      writer.close()
      return
    if len(self.buffers) > self.max_connections:
      logger.error(f"Max connection {self.max_connections} exceeded. ")
      writer.close()
      return

    ip, port = writer.get_extra_info('peername')
    message_id = get_connection_id((ip, port))
    self.buffers[message_id] = asyncio.Queue()

    await asyncio.wait([self.forward_buffer_msg(writer), self.forward_remote_msg(reader, writer)])

  async def run(self):
    server_client_serve = websockets.serve(self.server_client_serve, self.server_client_ip, self.server_client_port)

    server_remote_server = await asyncio.start_server(self.server_remote_serve, self.server_remote_ip, self.server_remote_port)
    server_remote_serve = server_remote_server.serve_forever()
    logger.debug(f"Server started at {(self.server_remote_ip, self.server_remote_port)}")
    await asyncio.gather(server_client_serve, server_remote_serve)