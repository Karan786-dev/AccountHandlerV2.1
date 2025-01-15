from pyrogram import Client , filters 
from config import cancelKeyboard
from ..responses.responseFunctions import createResponse
from middleware.checkAccess import checkAccess


@Client.on_callback_query(filters.regex(r'^/sendMessage'))
async def sendMessageHandler(_,query):
    if not await checkAccess(_,query):return 
    await query.message.edit(f"<b>📝 Enter The Message/Feedbacks (separate them with '|')</b>",reply_markup=cancelKeyboard)
    createResponse(query.from_user.id,"messageToSend")
