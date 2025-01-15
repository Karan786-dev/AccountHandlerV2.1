from pyrogram import Client, filters  # type: ignore
from markups import adminPanel
from middleware.authAdmin import authAdmin


@Client.on_message(filters.command(["admin", "panel", "adminPanel", "adminpanel"]))
async def handleAdminCommand(_, msg):
    if not authAdmin(_,msg):return
    text, keyboard = adminPanel(msg.from_user)
    await msg.reply(text, reply_markup=keyboard)
    pass
