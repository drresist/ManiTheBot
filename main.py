import os
from loguru import logger
import telebot
from config import Config
from bot.handlers import register_handlers
from web.flask_app import start_flask_app

config = Config()
token = os.getenv("TG_MANI_BOT")
if token is None:
    raise RuntimeError("TOKEN is not set")

bot = telebot.TeleBot(token)

if __name__ == "__main__":
    logger.info("Запуск бота")
    register_handlers(bot)
    start_flask_app()
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
