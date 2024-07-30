from loguru import logger
from telebot import types


def create_initial_keyboard():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(
        types.KeyboardButton("Expense"),
        types.KeyboardButton("Income"),
        types.KeyboardButton("Статистика"),
    )
    return markup


def create_category_keyboard(categories):
    markup = types.InlineKeyboardMarkup(row_width=2)
    for category in categories:
        markup.add(
            types.InlineKeyboardButton(
                category["category"], callback_data=str(category["id"])
            )
        )
    markup.add(types.InlineKeyboardButton("Назад", callback_data="back"))
    logger.debug(f"Created category keyboard: {markup}")
    return markup
