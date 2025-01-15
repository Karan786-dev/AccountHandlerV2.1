from pyrogram import Client , filters 
from ..responses.responseFunctions import createResponse
from config import cancelKeyboard
from middleware.checkAccess import checkAccess

@Client.on_callback_query(filters.regex(r'^/leaveChats'))
async def joinChatHandler(_,query):
    if not await checkAccess(_,query):return
    await query.message.edit("<b>🔈 Enter The Channel Links:</b>\nFor 2 or more channels: @chan1|@chan2|@chan3",reply_markup=cancelKeyboard)
    createResponse(query.from_user.id,"leaveChatID")