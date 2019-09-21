import pytest
import homes.protocol

def test_protocol():
  id, tag, data = 114514, homes.protocol.BEGIN, b'fuck you'
  b = homes.protocol.TCPMessage(id, homes.protocol.BEGIN, data).to_bytes()

  id2, tag2, data2 = homes.protocol.TCPMessage.from_bytes(b)

  assert id2 == id
  assert tag2 == tag
  assert data2 == data

  with pytest.raises(homes.protocol.BadTCPMessage):
    homes.protocol.TCPMessage.from_bytes(b'1' * (homes.protocol._head_size - 1))