import openai
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode, ReplyKeyboardMarkup, KeyboardButton
from config import CHAT_ID, OPENAI_TOKEN, TG_TOKEN, WEBHOOK_PATH, WEBHOOK_URL, WEBAPP_HOST, WEBAPP_PORT

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

# Словарь с ролями
roles_dict = {
    "Экономист": "Экономист, специализирующийся на макроэкономике",
    "Программист": "Программист, эксперт в Python и AI",
    "Историк": "Историк, специализирующийся на средних веках"
}

main_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
main_keyboard.add(KeyboardButton("Помощь"))
main_keyboard.add(KeyboardButton("Остановить"))
main_keyboard.add(KeyboardButton("Установить роль"))

async def generate_response(prompt_text: str) -> str:
    global user_role
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

@dp.message_handler(commands=['start'])
async def on_start(message: types.Message):
    global waiting_for_role
    await message.answer("Привет! Пожалуйста, укажите роль для бота.", reply_markup=main_keyboard)
    waiting_for_role = True
    logger.info(f"User {message.from_user.id} started the bot.")

@dp.message_handler(lambda message: message.text == "Установить роль")
async def prompt_role(message: types.Message):
    role_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    for role in roles_dict.keys():
        role_keyboard.add(KeyboardButton(role))
    await message.answer("Выберите роль из предложенных или введите свою.", reply_markup=role_keyboard)

@dp.message_handler(lambda message: waiting_for_role and message.text in roles_dict, content_types=types.ContentType.TEXT)
async def set_predefined_role(message: types.Message):
    global user_role, waiting_for_role
    user_role = roles_dict[message.text]
    waiting_for_role = False
    await message.answer(f"Роль установлена как: {user_role}. Теперь вы можете начать диалог!", reply_markup=main_keyboard)
    logger.info(f"User {message.from_user.id} set role as: {user_role}")

@dp.message_handler(lambda message: waiting_for_role, content_types=types.ContentType.TEXT)
async def set_custom_role(message: types.Message):
    global user_role, waiting_for_role
    user_role = message.text
    waiting_for_role = False
    await message.answer(f"Роль установлена как: {user_role}. Теперь вы можете начать диалог!", reply_markup=main_keyboard)
    logger.info(f"User {message.from_user.id} set role as: {user_role}")

@dp.message_handler(lambda message: message.text == "Остановить")
async def stop_bot(message: types.Message):
    await message.answer("Бот остановлен!", reply_markup=types.ReplyKeyboardRemove())
    logger.info(f"User {message.from_user.id} stopped the bot.")

@dp.message_handler(lambda message: message.text == "Помощь")
async def help_bot(message: types.Message):
    help_text = "Это бот на основе OpenAI. Вы можете установить роль для бота, после чего задавать ему вопросы."
    await message.answer(help_text, reply_markup=main_keyboard)

@dp.message_handler(lambda message: not waiting_for_role, content_types=types.ContentType.TEXT)
async def on_message(message: types.Message):
    global last_user_message
    user_message = message.text
    last_user_message = user_message
    logger.info(f"Received message from user {message.from_user.id}: {user_message}")

    response = await generate_response(user_message)
    await bot.send_message(CHAT_ID, response, parse_mode=ParseMode.MARKDOWN)

async def on_startup(dp):
    webhook_info = await bot.get_webhook_info()
    logger.info(f"Current webhook info: {webhook_info}")
    logger.info("Starting up...")
    try:
        await bot.send_message(CHAT_ID, "Bot has been started")
        await bot.set_webhook(WEBHOOK_URL)
        logger.info("Webhook set successfully!")
    except Exception as e:
        logger.error(f"Error setting up the webhook: {e}")

async def on_shutdown(dp):
    logger.info("Shutting down...")
    try:
        await bot.send_message(CHAT_ID, "Bot has been stopped")
        await bot.delete_webhook()
        logger.info("Webhook deleted successfully!")
    except Exception as e:
        logger.error(f"Error deleting the webhook: {e}")


if __name__ == '__main__':
    from aiogram import executor
    executor.start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
    )
# if __name__ == '__main__':
#     from aiogram import executor
#     executor.start_polling(dp, skip_updates=True)
