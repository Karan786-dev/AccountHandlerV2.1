from pyrogram import Client , filters
from pyrogram.types import CallbackQuery , InlineKeyboardButton ,InlineKeyboardMarkup
from markups import manageChannelMarkup , viewChannelManage
from ..responses.responseFunctions import createResponse
from config import cancelKeyboard
from database import Accounts , Channels
from functions import *


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
    
@Client.on_callback_query(filters.regex(r'^/toggle_spam_protection'))
async def spamProtectionHandler(_: Client,query: CallbackQuery):
    channelID = int(query.data.split(maxsplit=1)[1])
    channelData = Channels.find_one({"channelID":channelID})
    spamProtection = channelData.get("spamProtection")
    if not spamProtection: Channels.update_one({"channelID":channelID},{"$set":{"spamProtection":True}})
    else: Channels.update_one({"channelID":channelID},{"$unset":{"spamProtection":True}})
    text,keyboard = await viewChannelManage(channelID)
    await query.message.edit(text,reply_markup=keyboard)
    
    
@Client.on_callback_query(filters.regex(r'^/toggle_validity'))
async def toggleChannelValidity(_: Client,query: CallbackQuery):
    channelID = int(query.data.split(maxsplit=1)[1])
    channelData = Channels.find_one({"channelID":channelID})
    validityStatus= channelData.get("validity")
    if not validityStatus: Channels.update_one({"channelID":channelID},{"$set":{"validity":True}})
    else: Channels.update_one({"channelID":channelID},{"$unset":{"validity":True}})
    text , keyboard = await viewChannelManage(channelID)
    await query.message.edit(text,reply_markup=keyboard)

@Client.on_callback_query(filters.regex(r'^/add_days'))
async def addDaysToValidity(_: Client,query: CallbackQuery):
    channelID = int(query.data.split(maxsplit=1)[1])
    await query.message.edit("<b>Send amount of days you want to add..</b>")
    answer = (await _.wait_for_message(query.from_user.id))
    await answer.delete()
    if not is_number(answer.text): 
        await query.message.edit("<b>Please enter a valid amount.</b>")
        await query.answer("Enter a valid amount",show_alert=True)
        return await addDaysToValidity(_,query)
    
    Channels.update_one({"channelID":channelID},{"$inc":{"daysLeft":int(f"{answer.text}")}})
    text , keyboard = await viewChannelManage(channelID)
    await query.message.edit(text,reply_markup=keyboard)

@Client.on_callback_query(filters.regex(r'^/quickAddDays'))
async def quickAddDays(_: Client,query: CallbackQuery):
    queryData = (query.data.split(maxsplit=1)[1]).split(":")
    channelID = int(queryData[0])
    days = int(queryData[1])
    channelData = Channels.find_one_and_update({"channelID":channelID},{"$inc":{"daysLeft":days}},return_document=True)
    await query.message.edit(f"<b>[{channelData.get("title")}]: +{days} Days</b>",reply_markup=None)
    await query.answer(f"[{channelData.get("title")}]: +30 days")

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
    
@Client.on_callback_query(filters.regex(r'^/removeChannel'))
async def removeChannelHanlder(_,query:CallbackQuery):
    channelID = query.data.split(" ")[1]
    Channels.delete_one({"channelID":int(channelID)})
    await query.answer("Channel Removed")
    text , keyboard = await manageChannelMarkup(int(1))
    await query.message.edit(text,reply_markup=keyboard)
    