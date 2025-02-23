from pyrogram import Client, filters
from ..responses.responseFunctions import createResponse 
from config import cancelKeyboard

@Client.on_callback_query(filters.regex(r'/broadcast'))
async def askForBroadcastPost(_,query):
    await query.message.edit("<b>Send broadcast Post</b>",reply_markup=cancelKeyboard)
    createResponse(query.from_user.id,"askForBroadcast")