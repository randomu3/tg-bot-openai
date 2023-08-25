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

# Словари для хранения состояния каждого пользователя
user_roles = {}
last_user_messages = {}
known_users = {}

# Константы
ROLES_DICT = {
    "Программист": "Программист, эксперт в Python и AI",
    "Экономист": "Экономист, специализирующийся на макроэкономике",
    "Историк": "Историк, специализирующийся на средних веках",
}

MAIN_KEYBOARD = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
MAIN_KEYBOARD.add(*[KeyboardButton(btn) for btn in ["Установить роль", "Остановить", "Помощь"]])

def get_inline_keyboard():
    return InlineKeyboardMarkup().add(InlineKeyboardButton("Продолжи", callback_data="continue_dialog"))

async def generate_response(prompt_text: str, user_role: str) -> str:
    system_message = user_role or "Ученый который знает все способы заработка и понимает как работать с людьми"
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-16k-0613",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt_text}
            ]
        )
        return response.choices[0].message['content'].strip()
    except Exception as e:
        logger.error(f"Error generating response from OpenAI: {e}")
        return "Произошла ошибка при генерации ответа."
    
@dp.message_handler(commands=['start'])
async def on_start(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name

    if user_id in known_users:
        await message.answer(f"Снова привет, {user_name}! Установи роль, чтобы мог помочь тебе.", reply_markup=MAIN_KEYBOARD)
    else:
        known_users[user_id] = True
        await message.answer(f"Привет, {user_name}! Пожалуйста, укажите роль для бота.", reply_markup=MAIN_KEYBOARD)


@dp.message_handler(lambda message: message.text == "Установить роль")
async def prompt_role(message: types.Message):
    role_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    role_keyboard.add(*[KeyboardButton(role) for role in ROLES_DICT.keys()])
    await message.answer("Выберите роль из предложенных или введите свою.", reply_markup=role_keyboard)

@dp.message_handler(lambda message: message.text in ROLES_DICT)
async def set_predefined_role(message: types.Message):
    user_id = message.from_user.id
    user_roles[user_id] = ROLES_DICT[message.text]
    await message.answer(f"Роль установлена как: {user_roles[user_id]}. Теперь вы можете начать диалог!", reply_markup=MAIN_KEYBOARD)

@dp.message_handler(lambda message: message.text == "Остановить")
async def stop_bot(message: types.Message):
    await message.answer("Бот остановлен!", reply_markup=types.ReplyKeyboardRemove())

@dp.message_handler(lambda message: message.text == "Помощь")
async def help_bot(message: types.Message):
    await message.answer(START_TEXT, reply_markup=MAIN_KEYBOARD)

@dp.message_handler(content_types=types.ContentType.TEXT)
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    user_message = message.text
    last_user_messages[user_id] = user_message
    current_role = user_roles.get(user_id, "")
    response = await generate_response(user_message, current_role)
    await bot.send_message(CHAT_ID, response, parse_mode=ParseMode.MARKDOWN, reply_markup=get_inline_keyboard())

@dp.callback_query_handler(lambda c: c.data == "continue_dialog")
async def continue_dialog_callback(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    last_message = last_user_messages.get(user_id, "")
    current_role = user_roles.get(user_id, "")
    response = await generate_response(f"Что бы вы сказали дальше по теме: {last_message}?", current_role)
    await bot.send_message(user_id, response, reply_markup=get_inline_keyboard())

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
