from webserver.web_server import WebServer
import asyncio
import logging

logger = logging.getLogger(__name__)

_web_server = None

EMAIL = ""
PASSWORD = ""

async def run():
    await _web_server.account_utils.login(EMAIL, PASSWORD)
    interval = 20
    await _web_server.account_utils.send_update_data_periodic(interval)

if __name__ == '__main__':
    # Configura il logging
    logging.basicConfig(level=logging.DEBUG)
    logger.getChild("paho").setLevel(logging.WARNING)

    # Crea e avvia il WebServer
    _web_server = WebServer()
    _web_server.start()

    # Usa un singolo loop di eventi per gestire tutte le operazioni asincrone
    event_loop = asyncio.get_event_loop()
    event_loop.run_until_complete(run())

    # Mantieni il loop in esecuzione
    event_loop.run_forever()
