import os
from loguru import logger
import telebot
from telebot import types
from config import Config
from db import add_payment, get_categories, get_transactions
from diagrams import create_income_expense_bar_chart, create_income_expense_summary
from users import ALLOWED_USERS

config = Config()
token = os.getenv("TG_MANI_BOT")
if token is None:
    raise RuntimeError("TOKEN is not set")

bot = telebot.TeleBot(token)
selected_category_ids = {}


def is_user_allowed(user_id):
    return user_id in ALLOWED_USERS


def create_initial_keyboard():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(
        types.KeyboardButton("Expense"),
        types.KeyboardButton("Income"),
        types.KeyboardButton("Статистика")
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


def send_unauthorized_message(chat_id):
    bot.send_message(chat_id, "Вы не авторизованы для использования этого бота.")


def handle_start_command(message):
    user_id = message.from_user.id
    if not is_user_allowed(user_id):
        logger.warning(f"Неавторизованный пользователь {user_id} попытался запустить бота")
        send_unauthorized_message(message.chat.id)
        return

    markup = create_initial_keyboard()
    logger.debug(f"Пользователь {user_id} запустил бота")
    bot.send_message(message.chat.id, "Пожалуйста, выберите тип:", reply_markup=markup)
    logger.debug("Начальная клавиатура успешно отправлена")


def handle_stat_command(message):
    user_id = message.from_user.id
    if not is_user_allowed(user_id):
        logger.warning(f"Неавторизованный пользователь {user_id} попытался запросить статистику")
        send_unauthorized_message(message.chat.id)
        return

    logger.debug(f"Пользователь {user_id} запросил статистику")
    data = get_transactions()
    create_income_expense_bar_chart(data=data)
    bot.send_message(message.chat.id, create_income_expense_summary())
    bot.send_photo(message.chat.id, open("income_expense_last_30_days.png", "rb"))
    logger.debug("Статистика успешно отправлена")


def handle_callback_query(call):
    user_id = call.from_user.id
    logger.debug(f"Получен callback-запрос от пользователя {user_id}: {call.data}")
    if not is_user_allowed(user_id):
        logger.warning(f"Неавторизованный пользователь {user_id} попытался сделать выбор")
        bot.answer_callback_query(call.id, "Вы не авторизованы для использования этого бота.")
        return

    if call.data == "back":
        markup = create_initial_keyboard()
        bot.send_message(call.message.chat.id, "Выберите тип:", reply_markup=markup)
    else:
        handle_category_selection(call)


def handle_type_selection(message):
    user_id = message.from_user.id
    logger.debug(f"Пользователь {user_id} выбрал {message.text}")
    categories = get_categories()
    selected_categories = [
        category for category in categories
        if category["type"] == message.text
    ]
    logger.debug(f"Выбранные категории: {selected_categories}")
    markup = create_category_keyboard(selected_categories)
    bot.send_message(message.chat.id, "Выберите категорию:", reply_markup=markup)


def handle_category_selection(call):
    user_id = call.from_user.id
    category_id = call.data
    logger.debug(f"Пользователь {user_id} выбрал категорию ID: {category_id}")
    selected_category_ids[call.message.chat.id] = category_id
    try:
        bot.send_message(
            call.message.chat.id,
            f"Вы выбрали категорию ID: {category_id}. Пожалуйста, введите сумму:",
        )
        logger.debug(f"Отправлено сообщение пользователю {user_id} с запросом ввода суммы")
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения пользователю {user_id}: {str(e)}")
        bot.send_message(call.message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте еще раз.")


def handle_amount_input(message):
    user_id = message.from_user.id
    if not is_user_allowed(user_id):
        logger.warning(f"Неавторизованный пользователь {user_id} попытался ввести сумму")
        send_unauthorized_message(message.chat.id)
        return

    amount = message.text
    logger.debug(f"Введенная сумма: {amount}")
    chat_id = message.chat.id

    if chat_id in selected_category_ids:
        category_id = selected_category_ids[chat_id]
        try:
            add_payment(
                user_id=str(message.from_user.id),
                category_id=category_id,
                amount=amount,
            )
            bot.send_message(message.chat.id, "Платеж успешно добавлен.")
            markup = create_initial_keyboard()
            bot.send_message(message.chat.id, "Выберите следующее действие:", reply_markup=markup)
        except ValueError:
            logger.error(f"Введена некорректная сумма: {amount}")
            bot.send_message(message.chat.id, "Введена некорректная сумма. Пожалуйста, введите числовое значение.")
        except Exception as e:
            logger.error(f"Не удалось добавить платеж: {e}")
            bot.send_message(message.chat.id, "Не удалось добавить платеж. Пожалуйста, попробуйте еще раз.")
        finally:
            selected_category_ids.pop(chat_id, None)
    else:
        bot.send_message(message.chat.id, "Пожалуйста, сначала выберите категорию.")
        markup = create_initial_keyboard()
        bot.send_message(message.chat.id, "Выберите тип:", reply_markup=markup)


@bot.message_handler(commands=["start"])
def send_welcome(message):
    handle_start_command(message)


@bot.message_handler(content_types=["document"])
def command_handle_doc(message):
    bot.reply_to(message, "Документ получен!")


@bot.message_handler(commands=["stat"])
def send_stat(message):
    handle_stat_command(message)


@bot.callback_query_handler(func=lambda call: True)
def handle_selection(call):
    logger.info(f"Получен callback-запрос от пользователя {call.from_user.id}")
    logger.info(f"Данные callback: {call.data}")
    handle_callback_query(call)


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    if not is_user_allowed(user_id):
        logger.warning(f"Неавторизованный пользователь {user_id} попытался использовать бота")
        send_unauthorized_message(message.chat.id)
        return

    if message.text in ["Expense", "Income"]:
        handle_type_selection(message)
    elif message.text == "Статистика":
        handle_stat_command(message)
    else:
        handle_amount_input(message)


if __name__ == "__main__":
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
