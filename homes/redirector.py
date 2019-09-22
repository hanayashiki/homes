from abc import ABC, abstractmethod
from typing import *

import websockets
from websockets.protocol import WebSocketCommonProtocol
import asyncio
import logging
import queue
import traceback


logger = logging.getLogger("homes")

class InvalidState(Exception):

  def __str__(self):
    return f"<InvalidState msg={' '.join(self.args)!r}>"

class Redirector(ABC):

  """
  client <--[Ws client]--> Redirector <--[TCP remote]--> remote
  """

  def __init__(self, ws: Optional[WebSocketCommonProtocol]):
    self.ws = ws
    pass

  @abstractmethod
  async def run(self):
    pass