from pyrogram import Client,filters,types
from pyrogram.types import InlineKeyboardButton,InlineKeyboardMarkup
from database import *
from functions import *
from markups import *
from config import *
from ..responses.responseFunctions import *
import asyncio 
from dailyActivity import *

@Client.on_callback_query(filters.regex(r"^/DailyActivityChannels"))
async def manageDailyActivityQuery(bot: Client,query: types.CallbackQuery):
    dataSplit = query.data.split(maxsplit=1)
    page = int(dataSplit[1]) if len(dataSplit) > 1 else 1
    text , keyboard = await manageChannelActivityMarkup(page)
    await query.message.edit(text=text,reply_markup=keyboard)
    
@Client.on_callback_query(filters.regex(r"^/ChannelActivityView"))
async def viewChannelActivityQuery(bot: Client,query: types.CallbackQuery):
    channelID = query.data.split(maxsplit=1)[1]
    channelData = ActivityChannels.find_one({"channelID":int(channelID)})
    text , keyboard = await viewChannelActivity(int(channelID),channelData=channelData)
    await query.message.edit(text=text,reply_markup=keyboard)
    
@Client.on_callback_query(filters.regex(r'^/ChannelActivityAdd'))
async def addChannelActivityQuery(bot: Client,query: types.CallbackQuery):
    syncBot = Accounts.find_one({"syncBot":True})
    if not syncBot:
        text = "Please assign a syncer bot before adding any channel"
        try:
            await query.answer(text)
        except Exception as e:
            await query.reply(f"<b>{text}</b>")
    await query.message.delete()
    await query.message.reply("<b>Send Channel Link or username to activate daily activities</b>",reply_markup=cancelKeyboard)
    createResponse(query.from_user.id,"addChannelActivityLink")
    
@Client.on_callback_query(filters.regex(r'^/ChannelActivityDelete'))
async def deleteChannelActivityQuery(bot: Client,query: types.CallbackQuery):
    channelID = query.data.split(maxsplit=1)[1]
    await ActivityChannels.delete_one({"channelID":int(channelID)})
    text , keyboard = await manageChannelActivityMarkup()
    await query.message.edit(text=text,reply_markup=keyboard)
    
@Client.on_callback_query(filters.regex(r'^/ChannelActivityToggle'))
async def toggleChannelActivityQuery(bot: Client,query: types.CallbackQuery):
    channelID = query.data.split(maxsplit=1)[1]
    channelData = ActivityChannels.find_one({"channelID":int(channelID)})
    activityStatus = channelData.get("activityStatus",False)
    if activityStatus:
        ActivityChannels.update_one(
            {"channelID":int(channelID)},
            {"$set":{"activityStatus":False}}
        )
        await query.answer("Daily activity disabled")
    else:
        ActivityChannels.update_one(
            {"channelID":int(channelID)},
            {"$set":{"activityStatus":True}}
        )
        await query.answer("Daily activity enabled")
        asyncio.create_task(doActivity(int(channelID)))
    text , keyboard = await viewChannelActivity(int(channelID))
    await query.message.edit(text=text,reply_markup=keyboard)
    
@Client.on_callback_query(filters.regex(r'^/changeMinJoinDelay'))
async def changeMinJoinDelayQuery(bot: Client,query: types.CallbackQuery):
    channelID = query.data.split(maxsplit=1)[1]
    await query.message.delete()
    await query.message.reply("<b>Send new minimum join delay in seconds</b>",reply_markup=cancelKeyboard)
    minJoinDelay: str = (await bot.listen(query.message.chat.id)).text
    if minJoinDelay == cancelButtonText: 
        text , keyboard = await viewChannelActivity(int(channelID))
        return await query.message.reply(text=text,reply_markup=keyboard)
    elif not minJoinDelay.isdigit():
        await query.message.reply("<b>Invalid input, please try again</b>")
        return await changeMinJoinDelayQuery(bot,query)
    
    await query.message.reply("<b>Minimum join delay updated successfully</b>")
    ActivityChannels.update_one(
        {"channelID":int(channelID)},
        {"$set":{"minJoinDelay":int(minJoinDelay)}}
    )
    text , keyboard = await viewChannelActivity(int(channelID))
    await query.message.reply(text=text,reply_markup=keyboard)

@Client.on_callback_query(filters.regex(r'^/changeMaxJoinDelay'))
async def changeMaxJoinDelayQuery(bot: Client,query: types.CallbackQuery):
    channelID = query.data.split(maxsplit=1)[1]
    await query.message.delete()
    await query.message.reply("<b>Send new maximum join delay in seconds</b>",reply_markup=cancelKeyboard)
    maxJoinDelay: str = (await bot.listen(query.message.chat.id)).text
    if maxJoinDelay == cancelButtonText: 
        text , keyboard = await viewChannelActivity(int(channelID))
        return await query.message.reply(text=text,reply_markup=keyboard)
    elif not maxJoinDelay.isdigit():
        await query.message.reply("<b>Invalid input, please try again</b>")
        return await changeMaxJoinDelayQuery(bot,query)
    
    await query.message.reply("<b>Maximum join delay updated successfully</b>")
    ActivityChannels.update_one(
        {"channelID":int(channelID)},
        {"$set":{"maxJoinDelay":int(maxJoinDelay)}}
    )
    text , keyboard = await viewChannelActivity(int(channelID))
    await query.message.reply(text=text,reply_markup=keyboard)
    
@Client.on_callback_query(filters.regex(r'^/changeMinLeaveDelay'))
async def changeMinLeaveDelayQuery(bot: Client,query: types.CallbackQuery):
    channelID = query.data.split(maxsplit=1)[1]
    await query.message.delete()
    await query.message.reply("<b>Send new minimum leave delay in seconds</b>",reply_markup=cancelKeyboard)
    minLeaveDelay: str = (await bot.listen(query.message.chat.id)).text
    if minLeaveDelay == cancelButtonText: 
        text , keyboard = await viewChannelActivity(int(channelID))
        return await query.message.reply(text=text,reply_markup=keyboard)
    elif not minLeaveDelay.isdigit():
        await query.message.reply("<b>Invalid input, please try again</b>")
        return await changeMinLeaveDelayQuery(bot,query)
    
    await query.message.reply("<b>Minimum leave delay updated successfully</b>")
    ActivityChannels.update_one(
        {"channelID":int(channelID)},
        {"$set":{"minLeaveDelay":int(minLeaveDelay)}}
    )
    text , keyboard = await viewChannelActivity(int(channelID))
    await query.message.reply(text=text,reply_markup=keyboard)
    
    
@Client.on_callback_query(filters.regex(r'^/changeMaxLeaveDelay'))
async def changeMaxLeaveDelayQuery(bot: Client,query: types.CallbackQuery):
    channelID = query.data.split(maxsplit=1)[1]
    await query.message.delete()
    await query.message.reply("<b>Send new maximum leave delay in seconds</b>",reply_markup=cancelKeyboard)
    maxLeaveDelay: str = (await bot.listen(query.message.chat.id)).text
    if maxLeaveDelay == cancelButtonText: 
        text , keyboard = await viewChannelActivity(int(channelID))
        return await query.message.reply(text=text,reply_markup=keyboard)
    elif not maxLeaveDelay.isdigit():
        await query.message.reply("<b>Invalid input, please try again</b>")
        return await changeMaxLeaveDelayQuery(bot,query)
    
    await query.message.reply("<b>Maximum leave delay updated successfully</b>")
    ActivityChannels.update_one(
        {"channelID":int(channelID)},
        {"$set":{"maxLeaveDelay":int(maxLeaveDelay)}}
    )
    text , keyboard = await viewChannelActivity(int(channelID))
    await query.message.reply(text=text,reply_markup=keyboard)
    
@Client.on_callback_query(filters.regex(r'^/changeMuteProbability'))
async def changeMuteProbabilityQuery(bot: Client,query: types.CallbackQuery):
    channelID = query.data.split(maxsplit=1)[1]
    await query.message.delete()
    await query.message.reply("<b>Send new mute probability</b>",reply_markup=cancelKeyboard)
    muteProbability: str = (await bot.listen(query.message.chat.id)).text
    if muteProbability == cancelButtonText: 
        text , keyboard = await viewChannelActivity(int(channelID))
        return await query.message.reply(text=text,reply_markup=keyboard)
    elif not muteProbability.isdigit():
        await query.message.reply("<b>Invalid input, please try again</b>")
        return await changeMuteProbabilityQuery(bot,query)
    
    await query.message.reply("<b>Mute probability updated successfully</b>")
    ActivityChannels.update_one(
        {"channelID":int(channelID)},
        {"$set":{"muteProbability":int(muteProbability.replace("%",""))}}
    )
    text , keyboard = await viewChannelActivity(int(channelID))
    await query.message.reply(text=text,reply_markup=keyboard)
    
    