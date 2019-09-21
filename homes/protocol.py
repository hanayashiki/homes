import struct
from typing import *
import hashlib

_head_format = "!Qc"
_head_size = struct.calcsize(_head_format)

MID = 0
BEGIN = 1
END = 2

def get_connection_id(addr: Tuple[str, int]):
  return int.from_bytes(hashlib.md5(f'{addr[0]}:{addr[1]}'.encode('utf-8')).digest()[0:8], byteorder="big")

class BadTCPMessage(Exception):
  pass

class TCPMessage(NamedTuple):
  id: int
  tag: int
  data: bytes

  """
  id: marks a session
  tag: one of the tags
  data: payload data.
  """

  @classmethod
  def from_bytes(cls, b: bytes):
    if len(b) < _head_size:
      raise BadTCPMessage(f"Too short message of length {len(b)}")

    head = b[0:_head_size]
    data = b[_head_size:]
    id, tag = struct.unpack(_head_format, head)
    return TCPMessage(id=id,
                      tag=int.from_bytes(tag, byteorder='big', signed=False),
                      data=data)

  def to_bytes(self):
    return struct.pack(_head_format, self.id, self.tag.to_bytes(length=1, byteorder='big')) + self.data
