import os
import typing as tp

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.types import ParseMode
from aiogram.utils import executor

from utils import get_platform_searcher


AVAILABLE_PLATFORMS: tp.Tuple[str, ...] = ('Ökko', 'IVI (currently not available, pick Ökko, please)')
buttons = [types.KeyboardButton(platform_name) for platform_name in AVAILABLE_PLATFORMS]
keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
for button in buttons:
    keyboard = keyboard.add(button)
USER_PLATFORMS: tp.Dict[str, str] = {}

bot = Bot(token=os.environ['BOT_TOKEN'])
dp = Dispatcher(bot)


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message) -> None:
    """Start command"""
    await message.answer("Hi!\nI'm CinemaBot!\nI can help you find your favorite movies. To start with, select the "
                         "platform you are using to watch movies!", reply_markup=keyboard)


@dp.message_handler(commands=['help'])
async def send_instructions(message: types.Message) -> None:
    await message.answer(f"Hi!\nI'm CinemaBot!\nI can help you find your favorite movies.\n Currently selected platform"
                         f" is {USER_PLATFORMS[message.from_user.id]}.\n If you want to change it, use */platform*"
                         f" command", parse_mode=ParseMode.MARKDOWN)


@dp.message_handler(commands=['platform'])
async def change_platform(message: types.Message) -> None:
    """Platform command"""
    await message.answer("Please, select the platform you are using to watch movies! Currently selected platform"
                         f" is {USER_PLATFORMS[message.from_user.id]}", reply_markup=keyboard)


async def save_platform_and_reply(message: types.message) -> None:
    """Save selected by user platform"""
    global USER_PLATFORMS
    USER_PLATFORMS[message.from_user.id] = message.text
    await message.reply(f'Great! Now I am ready to search for movies in {message.text}.')


async def reply_with_movie_report(message: types.message) -> None:
    """Parse platform and answer with a movie report"""
    platform = USER_PLATFORMS[message.from_user.id]
    platform_searcher = get_platform_searcher(platform)
    movie_report = await platform_searcher(message)
    reply = ""
    if movie_report.title is not None:
        reply += f"*Title:* {movie_report.title}"
    else:
        await message.reply('Unfortunately, I could not find this movie in Ökko. Check for typos or try another one.')
        return
    if movie_report.alternative_title is not None:
        reply += f" ({movie_report.alternative_title})\n"
    else:
        reply += "\n"
    if movie_report.description is not None:
        reply += f"*Description:* {movie_report.description}\n"
    if movie_report.movie_link is not None:
        reply += f"*Link:* {movie_report.movie_link}"
    if movie_report.poster_link is not None:
        await bot.send_photo(message.from_user.id, movie_report.poster_link,
                             caption=reply,
                             reply_to_message_id=message.message_id,
                             parse_mode=ParseMode.MARKDOWN)
    else:
        await message.reply(reply, parse_mode=ParseMode.MARKDOWN)


@dp.message_handler()
async def echo(message: types.Message) -> None:
    if message.text in AVAILABLE_PLATFORMS:
        await save_platform_and_reply(message)
        return

    await reply_with_movie_report(message)


if __name__ == '__main__':
    executor.start_polling(dp)
