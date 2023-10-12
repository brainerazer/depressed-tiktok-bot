import asyncio
import json
import logging
import os
import io
import re
import base64
import sys
from os import getenv
from urllib.parse import urlparse

from aiogram import Bot, Dispatcher, Router, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.utils.markdown import hbold
from aiogram.types import URLInputFile, InputMediaPhoto, InputMediaAudio

from yt_dlp import YoutubeDL

import validators

# Bot token can be obtained via https://t.me/BotFather
TOKEN = getenv("BOT_TOKEN")

# All handlers should be attached to the Router (or Dispatcher)
dp = Dispatcher()

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def check_if_slideshow(url):
    with YoutubeDL() as ydl:
        result = ydl.extract_info(url, download=False)

        if result["formats"][0]["ext"] == ".mp3" or \
            result["formats"][0]["url"] == ".m4a" or \
            (not result["formats"][0]["width"] and not result["formats"][0]["height"]):
            # this is most likely a slideshow
            return True
        
    return False

# Taken from https://github.com/dylanpdx/vxtiktok/blob/main/vxtiktok.py
def get_slideshow_from_post_URL(url): # thsi function assumes the url is a slideshow
    with YoutubeDL(params={"dump_intermediate_pages":True}) as ydl:
        f = io.StringIO()
        ydl._out_files.screen = f # this is a hack to get the output of ydl to a variable
        result = ydl.extract_info(url, download=False)
        s=f.getvalue()
        # find the first line that's valid base64 data
        data=None
        for line in s.splitlines():
            if re.match(r"^[A-Za-z0-9+/=]+$", line):
                data= json.loads(base64.b64decode(line).decode())
        thisPost = data["aweme_list"][0]
        postMusicURL = thisPost["music"]["play_url"]["uri"]
        postImages = thisPost["image_post_info"]["images"]
        imageUrls=[]
        for image in postImages:
            for url in image["display_image"]["url_list"]:
                imageUrls.append(url)
                break

        finalData = {
            "musicURL": postMusicURL,
            "imageURLs": imageUrls
        }

        return finalData

async def download_and_reply(message: types.Message) -> None:
    parsed_url = urlparse(message.text)
    tt_slug = parsed_url.path.strip('/')
    ydl_opts = {
        'outtmpl': f'{tt_slug}.%(ext)s'
    }
    if not check_if_slideshow(message.text):
        with YoutubeDL(ydl_opts) as ydl:
            def download_video():
                info = ydl.extract_info('https://vm.tiktok.com/ZMjxG2hXV', download=False)
                return info['url']

            video_url = await asyncio.get_event_loop().run_in_executor(None, download_video)
            tg_file = URLInputFile(video_url)
            await message.reply_video(tg_file)

    else:
        loop = asyncio.get_event_loop()
        slideshow_data = await loop.run_in_executor(None, get_slideshow_from_post_URL, message.text)
        tg_images = [InputMediaPhoto(media=URLInputFile(x)) for x in slideshow_data['imageURLs']]
        tg_music = URLInputFile(slideshow_data['musicURL'])

        tg_images_chunked = list(chunks(tg_images, 10))
        await message.reply_media_group(tg_images_chunked[0])
        for chunk in tg_images_chunked:
            await message.answer_media_group(chunk)
        await message.answer_audio(tg_music)



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
        raise


async def main() -> None:
    # Initialize Bot instance with a default parse mode which will be passed to all API calls
    bot = Bot(TOKEN, parse_mode=ParseMode.HTML)
    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())