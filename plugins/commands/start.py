from pyrogram import Client, filters  # type: ignore
from database import Users
from middleware.checkUser import checkUser
from markups import mainMenu
from middleware.checkAccess import checkAccess

@Client.on_message(filters.command('start'))
async def start(_, msg):
    if not await checkUser(_, msg):
        return
    if not await checkAccess(_,msg):return
    text, keyboard = mainMenu(msg.from_user)
    await msg.reply(text, reply_markup=keyboard)
    pass
