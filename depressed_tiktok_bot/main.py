import asyncio
import json
import logging
import os
import sys
from os import getenv
from urllib.parse import urlparse

from aiogram import Bot, Dispatcher, Router, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.utils.markdown import hbold
from aiogram.types import FSInputFile

from yt_dlp import YoutubeDL

import validators

# Bot token can be obtained via https://t.me/BotFather
TOKEN = getenv("BOT_TOKEN")

# All handlers should be attached to the Router (or Dispatcher)
dp = Dispatcher()


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    This handler receives messages with `/start` command
    """
    # Most event objects have aliases for API methods that can be called in events' context
    # For example if you want to answer to incoming message you can use `message.answer(...)` alias
    # and the target chat will be passed to :ref:`aiogram.methods.send_message.SendMessage`
    # method automatically or call API method directly via
    # Bot instance: `bot.send_message(chat_id=message.chat.id, ...)`
    await message.answer(f"Hello, {hbold(message.from_user.full_name)}!")

async def download_and_reply(message: types.Message) -> None:
    parsed_url = urlparse(message.text)
    tt_slug = parsed_url.path.strip('/')
    ydl_opts = {
        'outtmpl': f'{tt_slug}.%(ext)s'
    }
    with YoutubeDL(ydl_opts) as ydl:
        def download_video():
            ydl.download([message.text])
        await asyncio.get_event_loop().run_in_executor(None, download_video)
        # ℹ️ ydl.sanitize_info makes the info json-serializable

    tg_file = FSInputFile(f'{tt_slug}.mp4')
    await message.reply_video(tg_file)
    os.remove(f'{tt_slug}.mp4')


@dp.message()
async def echo_handler(message: types.Message) -> None:
    """
    Handler will forward receive a message back to the sender

    By default, message handler will handle all message types (like a text, photo, sticker etc.)
    """
    try:
        if validators.url(message.text):
            parsed_url = urlparse(message.text)
            if parsed_url.scheme != 'https' or parsed_url.netloc != 'vm.tiktok.com':
                return
            
            await download_and_reply(message)
    except TypeError:
        # But not all the types is supported to be copied so need to handle it
        await message.answer("Nice try!")


async def main() -> None:
    # Initialize Bot instance with a default parse mode which will be passed to all API calls
    bot = Bot(TOKEN, parse_mode=ParseMode.HTML)
    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())