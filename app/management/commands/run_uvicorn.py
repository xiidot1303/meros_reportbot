from django.core.management.base import BaseCommand

import signal
import uvicorn
import asyncio
from bot.control.updater import application
from config import BOT_PORT as PORT

# This function will be called when a shutdown signal is received
def handle_shutdown(signal, frame):
    print("Received shutdown signal")
    # Stop the event loop
    loop = asyncio.get_event_loop()
    loop.stop()

# Register signal handlers for graceful shutdown
signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)

async def serve():
    config = uvicorn.Config("core.asgi:application", host="127.0.0.1", port=PORT, log_level="info")
    server = uvicorn.Server(config)
    # await server.serve()
    async with application:
        await application.start()
        await server.serve()
        await application.stop()

class Command(BaseCommand):
    help = 'Start uvicron server'

    def handle(self, *args, **options):
        try:
            asyncio.run(
                serve()
            )
        except KeyboardInterrupt:
            pass
