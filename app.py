from webserver.web_server import WebServer
import time
import asyncio
import logging


logger = logging.getLogger(__name__)


_web_server = None

EMAIL = "youremail@gmail.com"
PASSWORD = "yourPassword"

async def run():
    await _web_server.account_utils.login(EMAIL, PASSWORD)
    
if __name__ == '__main__':
    # Create and start the Flask server
    _web_server = WebServer()
    _web_server.start()
    event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(event_loop)
    cloud_client = event_loop.run_until_complete(run())

    interval = 10
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(_web_server.account_utils._lubaMQTT.send_update_data_periodic(interval))
    loop.run_forever()        