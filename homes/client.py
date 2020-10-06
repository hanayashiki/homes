import logging
from homes import utils
from homes.client_core import Client
import asyncio

logger = logging.getLogger("homes")
logging.basicConfig(format='%(asctime)s %(filename)16s %(funcName)32s : %(levelname)s  %(message)s')
logger.setLevel(logging.ERROR)

def run(conf: utils.Config):
  if conf.debug:
    logger.setLevel(logging.DEBUG)

  ssl_context = utils.get_ssl_context(conf, side="client")
  if conf.use_ssl:
    ssl_context.check_hostname = conf.check_hostname

  client = Client(client_local_addr=conf.client_local_addr,
                  server_client_addr=conf.server_client_addr,
                  ssl_context=ssl_context,
                  token=conf.token,
                  max_connections=conf.max_connections)

  asyncio.run(client.run(), debug=conf.debug)


if __name__ == '__main__':
  config = utils.import_config()

  run(config)
