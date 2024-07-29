from loguru import logger
from telebot import TeleBot
from bot.states import BotStateMachine, BotState
from bot.keyboards import create_initial_keyboard, create_category_keyboard
from database.operations import add_payment, get_categories, get_transactions
from utils.diagrams import create_income_expense_bar_chart, create_income_expense_summary
from utils.validators import is_user_allowed

state_machines = {}


def register_handlers(bot: TeleBot):
    @bot.message_handler(commands=['start'])
    def start_command(message):
        handle_start_command(bot, message)

    @bot.message_handler(commands=['stat'])
    def stat_command(message):
        handle_stat_command(bot, message)

    @bot.callback_query_handler(func=lambda call: True)
    def callback_query(call):
        handle_callback_query(bot, call)

    @bot.message_handler(func=lambda message: True)
    def message_handler(message):
        handle_message(bot, message)


def handle_start_command(bot: TeleBot, message):
    user_id = message.from_user.id
    if not is_user_allowed(user_id):
        logger.warning(f"Неавторизованный пользователь {user_id} попытался запустить бота")
        bot.send_message(message.chat.id, "Вы не авторизованы для использования этого бота.")
        return

    state_machines[user_id] = BotStateMachine()
    markup = create_initial_keyboard()
    logger.debug(f"Пользователь {user_id} запустил бота")
    bot.send_message(message.chat.id, "Пожалуйста, выберите тип:", reply_markup=markup)


def handle_stat_command(bot: TeleBot, message):
    user_id = message.from_user.id
    if not is_user_allowed(user_id):
        logger.warning(f"Неавторизованный пользователь {user_id} попытался запросить статистику")
        bot.send_message(message.chat.id, "Вы не авторизованы для использования этого бота.")
        return

    logger.debug(f"Пользователь {user_id} запросил статистику")
    data = get_transactions()
    create_income_expense_bar_chart(data=data)
    bot.send_message(message.chat.id, create_income_expense_summary())
    bot.send_photo(message.chat.id, open("income_expense_last_30_days.png", "rb"))


def handle_callback_query(bot: TeleBot, call):
    user_id = call.from_user.id
    if not is_user_allowed(user_id):
        logger.warning(f"Неавторизованный пользователь {user_id} попытался сделать выбор")
        bot.answer_callback_query(call.id, "Вы не авторизованы для использования этого бота.")
        return

    state_machine = state_machines.get(user_id)
    if not state_machine:
        state_machine = BotStateMachine()
        state_machines[user_id] = state_machine

    if call.data == "back":
        state_machine.transition_to(BotState.IDLE)
        markup = create_initial_keyboard()
        bot.send_message(call.message.chat.id, "Выберите тип:", reply_markup=markup)
    else:
        state_machine.transition_to(BotState.AWAITING_AMOUNT)
        state_machine.set_context('category_id', call.data)
        bot.send_message(call.message.chat.id, f"Вы выбрали категорию ID: {call.data}. Пожалуйста, введите сумму:")


def handle_message(bot: TeleBot, message):
    user_id = message.from_user.id
    if not is_user_allowed(user_id):
        logger.warning(f"Неавторизованный пользователь {user_id} попытался использовать бота")
        bot.send_message(message.chat.id, "Вы не авторизованы для использования этого бота.")
        return

    state_machine = state_machines.get(user_id)
    if not state_machine:
        state_machine = BotStateMachine()
        state_machines[user_id] = state_machine

    if state_machine.get_state() == BotState.IDLE:
        if message.text in ["Expense", "Income"]:
            handle_type_selection(bot, message, state_machine)
        elif message.text == "Статистика":
            handle_stat_command(bot, message)
    elif state_machine.get_state() == BotState.AWAITING_AMOUNT:
        handle_amount_input(bot, message, state_machine)


def handle_type_selection(bot: TeleBot, message, state_machine):
    categories = get_categories()
    selected_categories = [category for category in categories if category["type"] == message.text]
    markup = create_category_keyboard(selected_categories)
    state_machine.transition_to(BotState.AWAITING_CATEGORY)
    bot.send_message(message.chat.id, "Выберите категорию:", reply_markup=markup)


def handle_amount_input(bot: TeleBot, message, state_machine):
    amount = message.text
    category_id = state_machine.get_context('category_id')

    try:
        add_payment(user_id=str(message.from_user.id), category_id=category_id, amount=amount)
        bot.send_message(message.chat.id, "Платеж успешно добавлен.")
        state_machine.transition_to(BotState.IDLE)
        state_machine.clear_context()
        markup = create_initial_keyboard()
        bot.send_message(message.chat.id, "Выберите следующее действие:", reply_markup=markup)
    except ValueError:
        logger.error(f"Введена некорректная сумма: {amount}")
        bot.send_message(message.chat.id, "Введена некорректная сумма. Пожалуйста, введите числовое значение.")
    except Exception as e:
        logger.error(f"Не удалось добавить платеж: {e}")
        bot.send_message(message.chat.id, "Не удалось добавить платеж. Пожалуйста, попробуйте еще раз.")
        state_machine.transition_to(BotState.IDLE)
        state_machine.clear_context()
