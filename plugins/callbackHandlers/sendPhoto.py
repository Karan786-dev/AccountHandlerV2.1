from pyrogram import Client , filters
from ..responses.responseFunctions import createResponse
from middleware.checkAccess import checkAccess
from config import cancelKeyboard

@Client.on_callback_query(filters.regex(r"/sendPhoto"))
async def sendPhoto(client, query):
    if not await checkAccess(client,query):return 
    await query.message.edit(f"Send your photos <b>One by One</b>",reply_markup=cancelKeyboard)
    createResponse(query.from_user.id,"photosToSent")