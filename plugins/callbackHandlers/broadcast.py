from pyrogram import Client, filters
from ..responses.responseFunctions import createResponse 

@Client.on_callback_query(filters.regex(r'/broadcast'))
async def askForBroadcastPost(_,query):
    await query.message.edit("<b>Send broadcast Post</b>")
    createResponse(query.from_user.id,"askForBroadcast")