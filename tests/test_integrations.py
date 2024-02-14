import aiogram
import pytest

from depressed_tiktok_bot.main import echo_handler, download_and_reply

from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_download_and_reply_tiktok_video():
    message_mock = AsyncMock(aiogram.types.Message)
    message_mock.reply_video = AsyncMock(aiogram.types.Message.reply_video)
    url = 'https://vm.tiktok.com/ZM67qXDU6'

    res = await(download_and_reply(message_mock, url))

    message_mock.reply_video.assert_called_once()

    result_file, = message_mock.reply_video.call_args.args
    w = message_mock.reply_video.call_args.kwargs['width']
    h = message_mock.reply_video.call_args.kwargs['height']

    assert w == 1080
    assert h == 1918
    