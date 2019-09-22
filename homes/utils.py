import importlib.util
import sys
import logging
import dataclasses
from typing import *
import ssl

logger = logging.getLogger("homes")


@dataclasses.dataclass
class Config:
  debug: bool
  root_ca_pem: str
  localhost_pem: str

  client_local_addr: Tuple[str, int]
  server_client_addr: Tuple[str, int]
  server_remote_addr: Tuple[str, int]

  use_ssl: True
  token: str

  max_connections: int
  force_ipv4: bool

def get_ssl_context(conf: Config, side: str="client"):
  if conf.use_ssl:
    if side == "client":
      ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
      if conf.debug and conf.localhost_pem:
        ssl_context.load_verify_locations(conf.root_ca_pem)
    elif side == "server":
      ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
      if conf.debug and conf.localhost_pem:
        ssl_context.load_cert_chain(conf.localhost_pem)
    else:
      raise ValueError(f"Unknown side name: {side}")
  else:
    ssl_context = None

  return ssl_context

def import_config():
  if len(sys.argv) == 1:
    config_file = "config.py"
  elif len(sys.argv) == 2:
    _, config_file = sys.argv
  else:
    logger.fatal(f"Incorrect parameters. ")
    raise ValueError(f"Incorrect parameters. ")

  spec = importlib.util.spec_from_file_location("config", config_file)
  config = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(config)

  return Config(
    debug                 = config.debug,
    root_ca_pem           = config.root_ca_pem,
    localhost_pem         = config.localhost_pem,

    client_local_addr     = config.client_local_addr,
    server_client_addr    = config.server_client_addr,
    server_remote_addr    = config.server_remote_addr,

    use_ssl               = config.use_ssl,
    token                 = config.token,

    max_connections       = config.max_connections,
    force_ipv4            = config.force_ipv4,
  )
