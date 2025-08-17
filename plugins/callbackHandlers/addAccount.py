from pyrogram import Client, filters  # type: ignore
from ..responses.responseFunctions import createResponse
from config import cancelKeyboard


@Client.on_callback_query(filters.regex(r'^/add_account'))
async def addAccount(_, query):
    await query.message.delete()
    await query.message.reply("Send account phone number", reply_markup=cancelKeyboard)
    createResponse(query.from_user.id, "createBot_phoneNumber")
    pass


@Client.on_callback_query(filters.regex(r'^/add_session_file'))
async def addSessionFile(_, query):
    await query.message.delete()
    await query.message.reply("Send session files", reply_markup=cancelKeyboard)
    createResponse(query.from_user.id, "createBot_sessionFile")
    pass