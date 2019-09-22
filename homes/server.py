import logging
from homes import utils
from homes.server_core import Server
import ssl
import asyncio

logger = logging.getLogger("homes")
logging.basicConfig(format='%(asctime)s %(filename)16s %(funcName)32s : %(levelname)s  %(message)s')
logger.setLevel(logging.ERROR)

def run(conf: utils.Config):
  if conf.debug:
    logger.setLevel(logging.DEBUG)

  ssl_context = utils.get_ssl_context(conf, side="server")

  server = Server(server_client_addr=conf.server_client_addr,
                  server_remote_addr=conf.server_remote_addr,
                  ssl_context=ssl_context,
                  token=conf.token,
                  max_connections=conf.max_connections
                  )

  asyncio.run(server.run(), debug=conf.debug)

if __name__ == '__main__':
  config = utils.import_config()

  run(config)