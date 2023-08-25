import openai
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import ParseMode, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from config import CHAT_ID, OPENAI_API_KEY, API_TOKEN, START_TEXT

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Инициализация OpenAI и Aiogram
openai.api_key = OPENAI_API_KEY
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Словарь с ролями
ROLES_DICT = {
    "Программист": "Программист, эксперт в Python и AI",
    "Экономист": "Экономист, специализирующийся на макроэкономике",
    "Историк": "Историк, специализирующийся на средних веках",
}

# Клавиатура для основных команд
MAIN_KEYBOARD = ReplyKeyboardMarkup(resize_keyboard=True)
MAIN_KEYBOARD.add(KeyboardButton("Установить роль"))
MAIN_KEYBOARD.add(KeyboardButton("Остановить"))
MAIN_KEYBOARD.add(KeyboardButton("Помощь"))

# Словари для хранения состояния каждого пользователя
user_roles = {}
last_user_messages = {}

# Генерация ответа с помощью OpenAI
async def generate_response(prompt_text: str, user_role: str) -> str:
    system_message = user_role if user_role else "Ученый который знает все способы заработка и понимает как работать с людьми"
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-16k-0613",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt_text}
            ]
        )
        answer = response.choices[0].message['content'].strip()
        logger.info(f"Generated response: {answer}")
        return answer
    except Exception as e:
        logger.error(f"Error generating response from OpenAI: {e}")
        return "Произошла ошибка при генерации ответа."

# Создаем клавиатуру для интерактивных кнопок
def get_inline_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Продолжи", callback_data="continue_dialog"))
    return keyboard

# Обработчики сообщений и колбеков
@dp.message_handler(lambda message: message.text == "Остановить")
async def stop_bot(message: types.Message):
    await message.answer("Бот остановлен!", reply_markup=types.ReplyKeyboardRemove())
    logger.info(f"User {message.from_user.id} stopped the bot.")

@dp.message_handler(lambda message: message.text == "Помощь")
async def help_bot(message: types.Message):
    help_text = START_TEXT
    await message.answer(help_text, reply_markup=MAIN_KEYBOARD)

@dp.message_handler(commands=['start'])
async def on_start(message: types.Message):
    await message.answer("Привет! Пожалуйста, укажите роль для бота.", reply_markup=MAIN_KEYBOARD)
    logger.info(f"User {message.from_user.id} started the bot.")

@dp.message_handler(lambda message: message.text == "Установить роль")
async def prompt_role(message: types.Message):
    role_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    for role in ROLES_DICT.keys():
        role_keyboard.add(KeyboardButton(role))
    await message.answer("Выберите роль из предложенных или введите свою.", reply_markup=role_keyboard)

@dp.message_handler(lambda message: message.text in ROLES_DICT, content_types=types.ContentType.TEXT)
async def set_predefined_role(message: types.Message):
    user_id = message.from_user.id
    user_roles[user_id] = ROLES_DICT[message.text]
    await message.answer(f"Роль установлена как: {user_roles[user_id]}. Теперь вы можете начать диалог!", reply_markup=MAIN_KEYBOARD)
    logger.info(f"User {user_id} set role as: {user_roles[user_id]}")

@dp.message_handler(content_types=types.ContentType.TEXT)
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    user_message = message.text
    last_user_messages[user_id] = user_message
    logger.info(f"Received message from user {user_id}: {user_message}")

    current_role = user_roles.get(user_id, "")
    response = await generate_response(user_message, current_role)
    
    await bot.send_message(CHAT_ID, response, parse_mode=ParseMode.MARKDOWN, reply_markup=get_inline_keyboard())

@dp.callback_query_handler(lambda c: c.data == "continue_dialog")
async def continue_dialog_callback(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    last_message = last_user_messages.get(user_id, "")
    current_role = user_roles.get(user_id, "")
    
    # Генерируем ответ на основе последнего сообщения пользователя
    response = await generate_response(f"Что бы вы сказали дальше по теме: {last_message}?", current_role)
    await bot.send_message(user_id, response, reply_markup=get_inline_keyboard())

# Запуск бота
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
