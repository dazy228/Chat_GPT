import logging
import openai
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import ParseMode
from aiogram.utils import executor
from requests.exceptions import RequestException

API_TOKEN = "5997705184:AAGe_coFjyXxsagmAwcNTzvvTniyTux8j6Y"
OPENAI_API_KEY = "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"

# Настройка OpenAI API
openai.api_key = OPENAI_API_KEY

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

async def get_gpt_response(prompt):
    messages = [
        {"role": "system", "content": "You are a helpful assistant that helps users improve their spoken English."},
        {"role": "user",
         "content": "recognize errors in sentences in English, offer options and give explanations in Russian"},
        {"role": "user",
         "content": "write the answer in English and below through write the translation in Russian and write down for each mistake in the sentence why you changed it."},
        {"role": "user", "content": "переводи все свои ответы ниже на русский, пожалуйста."},
        {"role": "assistant", "content": "Ok, i understand you"},
        {"role": "user", "content": "Я принимал душ вчера вечером"},
        {"role": "assistant", "content": """Исправлено: I took a shower yesterday evening."

Перевод: Я принял душ вчера вечером.

Объяснение: "Принимал" использовано в неправильной форме прошедшего времени. Правильной формой будет "took" ."""},
        {"role": "user", "content": prompt}
    ]
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
    )
    return completion.choices[0].message.content

@dp.message_handler(commands=["start", "help"])
async def send_welcome(message: types.Message):
    welcome_text = (
        "Привет! Я бот-тренер для английского. "
        "Напиши мне предложение на английском или на русском, и я помогу тебе перевести или улучшить свои навыки английского языка, "
        "исправляя ошибки и предлагая альтернативные формулировки."
    )
    await message.reply(welcome_text)


@dp.message_handler()
async def handle_message(message: types.Message):
    try:
        response = await get_gpt_response(message.text)
        first_name = message.from_user.first_name or "none_first name"
        username = message.from_user.username or "none_username"
        print('[*] ' + username + '   (' + first_name + ') \n')
        print(f' - {message.text}\n')
        words = response.split()
        response_blocks = [words[i:i + 10] for i in range(0, len(words), 13)]
        for block in response_blocks:
            block_text = ' '.join(block)
            print(block_text)
        print('-' * len(response))
        await message.reply(response)
    except RequestException as e:
        logging.error(f"Internet error occurred: {e}")
        await asyncio.sleep(10)  # Pause before trying again
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        await asyncio.sleep(10)  # Pause before trying again

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
