from pyrogram import Client , filters
from pyrogram.types import CallbackQuery , InlineKeyboardButton ,InlineKeyboardMarkup
from markups import manageChannelMarkup , viewChannelManage
from ..responses.responseFunctions import createResponse
from config import cancelKeyboard
from database import Accounts


@Client.on_callback_query(filters.regex(r'^/manageChannels'))
async def manageChannelsHandler(_,query:CallbackQuery):
    queryParams = query.data.split(maxsplit=1)
    pageNo = queryParams[1] if len(queryParams) == 2 else 1
    text , keyboard = await manageChannelMarkup(int(pageNo))
    await query.message.edit(text,reply_markup=keyboard)
    
@Client.on_callback_query(filters.regex(r'^/viewChannel'))
async def viewChannelHandler(_,query:CallbackQuery):
    channelID= int(query.data.split(maxsplit=1)[1])
    text , keyboard = await  viewChannelManage(channelID)
    await query.message.edit(text,reply_markup=keyboard)

@Client.on_callback_query(filters.regex(r'^/addChannel'))
async def addChannelHandler(_,query:CallbackQuery):
    syncBot = Accounts.find_one({"syncBot":True})
    if not syncBot:
        text = "Please assign a syncer bot before adding any channel"
        try:
            await query.answer(text)
        except Exception as e:
            await query.reply(f"<b>{text}</b>")
    await query.message.delete()
    await query.message.reply("<b>Send Channel Link or username</b>",reply_markup=cancelKeyboard)
    createResponse(query.from_user.id,"addChannelLink")
    
