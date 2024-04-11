import os
# from dotenv import load_dotenv
from loguru import logger
import telebot
from telebot import types

from config import Config
from db import add_payment, get_categories, get_transactions
from diagrams import create_income_expense_bar_chart, create_income_expense_summary
from users import ALLOWED_USERS

# load_dotenv()

config = Config()
token = os.getenv('TG_MANI_BOT')
if token is None:
    raise RuntimeError("TOKEN is not set")

bot = telebot.TeleBot(token)
selected_category_ids = {}

def is_user_allowed(user_id):
    return user_id in ALLOWED_USERS

def create_initial_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("Expense", callback_data='expense'),
               types.InlineKeyboardButton("Income", callback_data='income'))
    return markup

def create_category_keyboard(categories):
    markup = types.InlineKeyboardMarkup(row_width=2)
    for category in categories:
        markup.add(types.InlineKeyboardButton(category['category'], callback_data=str(category['id'])))
    logger.debug(f"Created category keyboard: {markup}")
    return markup

def send_unauthorized_message(chat_id):
    bot.send_message(chat_id, "You are not authorized to use this bot.")

def handle_start_command(message):
    user_id = message.from_user.id
    if not is_user_allowed(user_id):
        logger.warning(f"Unauthorized user {user_id} tried to start the bot")
        send_unauthorized_message(message.chat.id)
        return

    markup = create_initial_keyboard()
    logger.debug(f"User {user_id} started the bot")
    bot.send_message(message.chat.id, "Please select a type:", reply_markup=markup)
    logger.debug("Initial keyboard sent successfully")
    logger.debug(f"Created initial keyboard: {markup}")

def handle_stat_command(message):
    user_id = message.from_user.id
    if not is_user_allowed(user_id):
        logger.warning(f"Unauthorized user {user_id} tried to request stat")
        send_unauthorized_message(message.chat.id)
        return

    logger.debug(f"User {user_id} requested stat")
    data = get_transactions()
    create_income_expense_bar_chart(data=data)
    bot.send_message(message.chat.id, create_income_expense_summary())
    bot.send_photo(message.chat.id, open('income_expense_last_30_days.png', 'rb'))
    logger.debug("Stat sent successfully")

def handle_callback_query(call):
    user_id = call.from_user.id
    logger.debug(f"Received callback query from user {user_id}: {call.data}")

    if not is_user_allowed(user_id):
        logger.warning(f"Unauthorized user {user_id} tried to make a selection")
        bot.answer_callback_query(call.id, "You are not authorized to use this bot.")
        return

    if call.data in ['expense', 'income']:
        handle_type_selection(call)
    else:
        handle_category_selection(call)

def handle_type_selection(call):
    user_id = call.from_user.id
    logger.debug(f"User {user_id} selected {call.data}")
    categories = get_categories()
    selected_categories = [category for category in categories if category['type'] == call.data.capitalize()]
    logger.debug(f"Selected categories: {selected_categories}")
    markup = create_category_keyboard(selected_categories)

    try:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text="Please select a category:", reply_markup=markup)
        logger.debug(f"Edited message text for user {user_id}")
    except Exception as e:
        logger.error(f"Error editing message text for user {user_id}: {str(e)}")
        bot.send_message(call.message.chat.id, "An error occurred. Please try again.")

def handle_category_selection(call):
    user_id = call.from_user.id
    category_id = call.data
    logger.debug(f"User {user_id} selected category ID: {category_id}")
    selected_category_ids[call.message.chat.id] = category_id

    try:
        bot.send_message(call.message.chat.id,
                         f"You selected category ID: {category_id}. Please enter the amount of money:")
        logger.debug(f"Sent message to user {user_id} requesting amount input")
    except Exception as e:
        logger.error(f"Error sending message to user {user_id}: {str(e)}")
        bot.send_message(call.message.chat.id, "An error occurred. Please try again.")

def handle_amount_input(message):
    user_id = message.from_user.id
    if not is_user_allowed(user_id):
        logger.warning(f"Unauthorized user {user_id} tried to input an amount")
        send_unauthorized_message(message.chat.id)
        return

    amount = message.text
    logger.debug(f"Amount entered: {amount}")
    chat_id = message.chat.id
    if chat_id in selected_category_ids:
        category_id = selected_category_ids[chat_id]
        try:
            amount = float(amount)
            add_payment(user_id=str(message.from_user.id), category_id=category_id, amount=amount)
            bot.send_message(message.chat.id, "Payment added successfully.")
        except ValueError as e:
            logger.error(f"Invalid amount entered: {amount}")
            bot.send_message(message.chat.id, "Invalid amount entered. Please enter a valid numeric value.")
        except Exception as e:
            logger.error(f"Failed to add payment: {e}")
            bot.send_message(message.chat.id, "Failed to add payment. Please try again.")
        finally:
            selected_category_ids.pop(chat_id, None)
    else:
        bot.send_message(message.chat.id, "Please select a category first.")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    handle_start_command(message)

@bot.message_handler(commands=['stat'])
def send_stat(message):
    handle_stat_command(message)

@bot.callback_query_handler(func=lambda call: True)
def handle_selection(call):
    logger.info(f"Received callback query from user {call.from_user.id}")
    logger.info(f"Callback data: {call.data}")
    handle_callback_query(call)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    handle_amount_input(message)

if __name__ == '__main__':
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
