import asyncio
import logging
import sys

# Ensure UTF-8 output on Windows terminal
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import BotCommand, BotCommandScopeDefault, MenuButtonWebApp, WebAppInfo

from config import BOT_TOKEN
from database import db
from handlers import user_router, relay_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

import os
from aiohttp import web

WEBAPP_URL = "https://akkiservices-bot.onrender.com"

async def handle_webapp_index(request):
    return web.FileResponse("webapp/index.html")

async def handle_health(request):
    return web.Response(text="OK", status=200)

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_webapp_index)
    app.router.add_get("/health", handle_health)
    if os.path.exists("webapp"):
        app.router.add_static("/static/", path="webapp", name="static")
    
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", "10000"))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Web server successfully bound to 0.0.0.0:{port}")

async def setup_bot_commands(bot: Bot):
    try:
        # Delete slash commands menu suggestions (/start, /myid)
        await bot.delete_my_commands(scope=BotCommandScopeDefault())
        # Retain WebApp persistent store button
        await bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(
                text="📱 Store",
                web_app=WebAppInfo(url=WEBAPP_URL)
            )
        )
        logger.info("Slash commands deleted and WebApp button registered successfully.")
    except Exception as e:
        logger.warning(f"Failed to update bot commands menu: {e}")

async def main():
    logger.info("Initializing Database...")
    await db.init_db()

    # Start Aiohttp Web Server for Render Port Binding & Mini App Hosting
    try:
        await start_web_server()
    except Exception as e:
        logger.warning(f"Could not start web server: {e}")

    logger.info("Starting AKKI SERVICES Telegram Bot...")
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
    )
    dp = Dispatcher()

    # Register Routers
    dp.include_router(user_router)
    dp.include_router(relay_router)

    await setup_bot_commands(bot)

    # Delete any pending webhook updates and drop old messages
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Bot is now ONLINE and polling for updates! 🚀")

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        logger.info("Bot stopped.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot shutdown completed.")
