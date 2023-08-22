import openai
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
from config import CHAT_ID, OPENAI_TOKEN, TG_TOKEN

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
    return response.choices[0].message['content'].strip()

@dp.message_handler(commands=['start'])
async def on_start(message: types.Message):
    global waiting_for_role
    await message.answer("Привет! Пожалуйста, укажите роль для бота.")
    waiting_for_role = True

@dp.message_handler(lambda message: waiting_for_role, content_types=types.ContentType.TEXT)
async def set_role(message: types.Message):
    global user_role, waiting_for_role
    user_role = message.text
    waiting_for_role = False
    await message.answer(f"Роль установлена как: {user_role}. Теперь вы можете начать диалог!")

@dp.message_handler(commands=['stop'])
async def on_stop(message: types.Message):
    await message.answer("Бот остановлен!")

@dp.message_handler(lambda message: not waiting_for_role, content_types=types.ContentType.TEXT)
async def on_message(message: types.Message):
    global last_user_message
    user_message = message.text
    last_user_message = user_message

    response = await generate_response(user_message)
    await bot.send_message(CHAT_ID, response, parse_mode=ParseMode.MARKDOWN)

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
