import openai
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode, ReplyKeyboardMarkup, KeyboardButton
from config import CHAT_ID, OPENAI_API_KEY, API_TOKEN, WEBHOOK_PATH, WEBHOOK_URL, WEBAPP_HOST, WEBAPP_PORT, START_TEXT

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

# Обработчики сообщений
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
    global user_role  # Добавьте эту строку
    user_role = ROLES_DICT[message.text]
    await message.answer(f"Роль установлена как: {user_role}. Теперь вы можете начать диалог!", reply_markup=MAIN_KEYBOARD)
    logger.info(f"User {message.from_user.id} set role as: {user_role}")

@dp.message_handler(content_types=types.ContentType.TEXT)
async def handle_message(message: types.Message):
    user_message = message.text
    logger.info(f"Received message from user {message.from_user.id}: {user_message}")

    response = await generate_response(user_message, user_role)
    await bot.send_message(CHAT_ID, response, parse_mode=ParseMode.MARKDOWN)

# Обработчики жизненного цикла бота
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

# Запуск бота
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
