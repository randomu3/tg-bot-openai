import openai
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
from config import CHAT_ID, OPENAI_TOKEN, TG_TOKEN

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

API_TOKEN = TG_TOKEN
OPENAI_API_KEY = OPENAI_TOKEN

openai.api_key = OPENAI_API_KEY

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

last_user_message = None
user_role = None
waiting_for_role = False

async def generate_response(prompt_text: str) -> str:
    global user_role
    system_message = user_role if user_role else "Ученый который знает все способы заработка и понимает как работать с людьми"
    
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

@dp.message_handler(commands=['start'])
async def on_start(message: types.Message):
    global waiting_for_role
    await message.answer("Привет! Пожалуйста, укажите роль для бота.")
    waiting_for_role = True
    logger.info(f"User {message.from_user.id} started the bot.")

@dp.message_handler(lambda message: waiting_for_role, content_types=types.ContentType.TEXT)
async def set_role(message: types.Message):
    global user_role, waiting_for_role
    user_role = message.text
    waiting_for_role = False
    await message.answer(f"Роль установлена как: {user_role}. Теперь вы можете начать диалог!")
    logger.info(f"User {message.from_user.id} set role as: {user_role}")

@dp.message_handler(commands=['stop'])
async def on_stop(message: types.Message):
    await message.answer("Бот остановлен!")
    logger.info(f"User {message.from_user.id} stopped the bot.")

@dp.message_handler(lambda message: not waiting_for_role, content_types=types.ContentType.TEXT)
async def on_message(message: types.Message):
    global last_user_message
    user_message = message.text
    last_user_message = user_message
    logger.info(f"Received message from user {message.from_user.id}: {user_message}")

    response = await generate_response(user_message)
    await bot.send_message(CHAT_ID, response, parse_mode=ParseMode.MARKDOWN)

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
