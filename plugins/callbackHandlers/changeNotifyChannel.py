from pyrogram import Client, filters
from pyrogram.types import CallbackQuery 
from ..responses.responseFunctions import createResponse
from config import cancelKeyboard

@Client.on_callback_query(filters.regex(r'^/notifyChangeChat'))
async def notifyChangeChatHandler(_:Client,query:CallbackQuery):
    await query.message.delete()
    await query.message.reply("<b>🔈 Enter The Channel Invite Link or Username:</b>",reply_markup=cancelKeyboard)
    createResponse(query.from_user.id,"notifyChangeChatGetID")