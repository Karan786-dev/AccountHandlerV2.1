from pyrogram import Client, filters  # type: ignore
from middleware.authAdmin import authAdmin
from markups import adminPanel


@Client.on_callback_query(filters.regex(r'^admin'))
async def adminPanel_Callback(_, query):
    text, keyboard = adminPanel(query.from_user)
    await query.message.edit(text, reply_markup=keyboard)
    pass
