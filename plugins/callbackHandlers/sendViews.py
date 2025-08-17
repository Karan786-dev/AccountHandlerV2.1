from pyrogram import Client , filters 
from config import cancelKeyboard
from ..responses.responseFunctions import createResponse
from middleware.checkAccess import checkAccess

@Client.on_callback_query(filters.regex(r'^/sendViews'))
async def sendViewsHandler(_,query):
    if not await checkAccess(_,query):return
    await query.message.edit("<b>👀 Enter The Post Link:</b>",reply_markup=cancelKeyboard)
    createResponse(query.from_user.id,"postLinkTosendViews")