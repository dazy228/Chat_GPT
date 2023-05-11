from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import Bot, Dispatcher, executor
from aiogram.utils.exceptions import NetworkError
from aiogram import Bot, Dispatcher, executor, types
from collections import deque
import openai
import asyncio
import openai.error
import logging
import time
from config import *

openai.api_key = OPENAI_API_KEY
bot = Bot(token=TELEGRAM_BOT_TOKEN)

dp = Dispatcher(bot)

logging.basicConfig(level=logging.INFO)
user_dialogs = {}
user_request_counter = {}
request_limit = 5
MAX_DIALOG_HISTORY = 5
time_window = 60

async def rate_limiter(user_id):
    if user_id not in user_request_counter:
        user_request_counter[user_id] = {'count': 1, 'timer': asyncio.get_event_loop().create_task(reset_counter(user_id))}
    else:
        user_request_counter[user_id]['count'] += 1
    if user_request_counter[user_id]['count'] > request_limit:
        return False
    return True

async def reset_counter(user_id):
    await asyncio.sleep(time_window)
    del user_request_counter[user_id]

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_dialogs:
        user_dialogs[user_id] = []

    await message.reply(f"Привет {message.from_user.first_name}! Я умный бот. Чем могу вам помочь?")

async def ai(prompt, user_id):
    # Историю диалога для каждого пользователя
    user_dialogs[user_id].append({"role": "user", "content": prompt})

    # Ограничение количество сообщений в истории диалога
    limited_dialog_history = list(user_dialogs[user_id])[-MAX_DIALOG_HISTORY:]

    try:
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=limited_dialog_history
        )
        return completion.choices[0].message.content
    except openai.error.APIConnectionError as e:
        logging.error(f"APIConnectionError occurred: {e}")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return None

@dp.message_handler()
async def echo(message: types.Message):
    user_id = message.from_user.id

    # Инициализация историю диалога для новых пользователей
    if user_id not in user_dialogs:
        user_dialogs[user_id] = deque([], maxlen=2 * MAX_DIALOG_HISTORY)

    # Проверка ограничение
    can_proceed = await rate_limiter(user_id)

    if not can_proceed:
        await message.reply(f'⚠️   Вы превысили лимит запросов в {request_limit} за {time_window} секунд.'
                            f' Пожалуйста, подождите.')
        return

    answer = await ai(message.text, user_id)

    if answer is not None:
        # Добавить ответы бота в историю диалога каждого пользователя
        user_dialogs[user_id].append({"role": "assistant", "content": answer})
        first_name = message.from_user.first_name or "none_first name"
        username = message.from_user.username or "none_username"
        print('[*] ' + username + '   (' + first_name + ') \n')
        print(f' - {message.text}\n')

        words = answer.split()
        answer_blocks = [words[i:i + 10] for i in range(0, len(words), 13)]
        for block in answer_blocks:
            block_text = ' '.join(block)
            print(block_text)
        print('-' * 90)
        await message.reply(answer)
    else:
        await message.reply('😞  Неизвестная ошибка, попробуйте ещё раз.')

async def main():
    while True:
        try:
            await dp.start_polling()
        except NetworkError as e:
            logging.error(f"Network error occurred: {e}")
            logging.info("Waiting for 5 seconds before restarting...")
            time.sleep(5)
        except TerminatedByOtherGetUpdates as e:
            logging.error(f"Terminated by other getUpdates request: {e}")
            logging.info("Waiting for 10 seconds before restarting...")
            time.sleep(10)
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            logging.info("Waiting for 10 seconds before restarting...")
            time.sleep(10)

if __name__ == '__main__':
    asyncio.run(main())
