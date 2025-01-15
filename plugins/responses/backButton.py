from pyrogram import Client, filters, ContinuePropagation  # type: ignore
from pyrogram.types import ReplyKeyboardRemove  # type: ignore
from config import cancelButtonText
from .responseFunctions import deleteResponse
from markups import mainMenu


@Client.on_message(filters.private)
async def backButton(_, msg):
    if msg.text != cancelButtonText:
        raise ContinuePropagation
    deleteResponse(msg.from_user.id)
    await msg.reply("You'r back !!!", reply_markup=ReplyKeyboardRemove())
    text, keyboard = mainMenu(msg.from_user)
    await msg.reply(text, reply_markup=keyboard)
