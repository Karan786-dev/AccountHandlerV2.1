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
    ActivityChannels.delete_one({"channelID":int(channelID)})
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
    
@Client.on_callback_query(filters.regex(r'^/changeMinJoin'))
async def changeMinJoinDelayQuery(bot: Client,query: types.CallbackQuery):
    channelID = query.data.split(maxsplit=1)[1]
    try: await query.message.delete()
    except: pass
    await query.message.reply("<b>Send new minimum joining/b>",reply_markup=cancelKeyboard)
    minJoin: str = (await bot.listen(query.message.chat.id)).text
    if minJoin == cancelButtonText: 
        text , keyboard = await viewChannelActivity(int(channelID))
        return await query.message.reply(text=text,reply_markup=keyboard)
    elif not minJoin.isdigit():
        await query.message.reply("<b>Invalid input, please try again</b>")
        return await changeMinJoinDelayQuery(bot,query)
    
    await query.message.reply("<b>Minimum joining updated successfully</b>")
    ActivityChannels.update_one(
        {"channelID":int(channelID)},
        {"$set":{"minimumJoin":int(minJoin)}}
    )
    text , keyboard = await viewChannelActivity(int(channelID))
    await query.message.reply(text=text,reply_markup=keyboard)

@Client.on_callback_query(filters.regex(r'^/changeMaxJoin'))
async def changeMaxJoinDelayQuery(bot: Client,query: types.CallbackQuery):
    channelID = query.data.split(maxsplit=1)[1]
    await query.message.delete()
    await query.message.reply("<b>Send new maximum joining</b>",reply_markup=cancelKeyboard)
    maxJoin: str = (await bot.listen(query.message.chat.id)).text
    if maxJoin == cancelButtonText: 
        text , keyboard = await viewChannelActivity(int(channelID))
        return await query.message.reply(text=text,reply_markup=keyboard)
    elif not maxJoin.isdigit():
        await query.message.reply("<b>Invalid input, please try again</b>")
        return await changeMaxJoinDelayQuery(bot,query)
    
    await query.message.reply("<b>Maximum joining updated successfully</b>")
    ActivityChannels.update_one(
        {"channelID":int(channelID)},
        {"$set":{"maximumJoin":int(maxJoin)}}
    )
    text , keyboard = await viewChannelActivity(int(channelID))
    await query.message.reply(text=text,reply_markup=keyboard)
    
@Client.on_callback_query(filters.regex(r'^/changeMinLeave'))
async def changeMinLeaveDelayQuery(bot: Client,query: types.CallbackQuery):
    channelID = query.data.split(maxsplit=1)[1]
    await query.message.delete()
    await query.message.reply("<b>Send new minimum leaving</b>",reply_markup=cancelKeyboard)
    minLeave: str = (await bot.listen(query.message.chat.id)).text
    if minLeave == cancelButtonText: 
        text , keyboard = await viewChannelActivity(int(channelID))
        return await query.message.reply(text=text,reply_markup=keyboard)
    elif not minLeave.isdigit():
        await query.message.reply("<b>Invalid input, please try again</b>")
        return await changeMinLeaveDelayQuery(bot,query)
    
    await query.message.reply("<b>Minimum leaving updated successfully</b>")
    ActivityChannels.update_one(
        {"channelID":int(channelID)},
        {"$set":{"minimumLeave":int(minLeave)}}
    )
    text , keyboard = await viewChannelActivity(int(channelID))
    await query.message.reply(text=text,reply_markup=keyboard)
    
    
@Client.on_callback_query(filters.regex(r'^/changeMaxLeave'))
async def changeMaxLeaveDelayQuery(bot: Client,query: types.CallbackQuery):
    channelID = query.data.split(maxsplit=1)[1]
    await query.message.delete()
    await query.message.reply("<b>Send new maximum leaving</b>",reply_markup=cancelKeyboard)
    maxLeave: str = (await bot.listen(query.message.chat.id)).text
    if maxLeave == cancelButtonText: 
        text , keyboard = await viewChannelActivity(int(channelID))
        return await query.message.reply(text=text,reply_markup=keyboard)
    elif not maxLeave.isdigit():
        await query.message.reply("<b>Invalid input, please try again</b>")
        return await changeMaxLeaveDelayQuery(bot,query)
    
    await query.message.reply("<b>Maximum leaving updated successfully</b>")
    ActivityChannels.update_one(
        {"channelID":int(channelID)},
        {"$set":{"maximumLeave":int(maxLeave)}}
    )
    text , keyboard = await viewChannelActivity(int(channelID))
    await query.message.reply(text=text,reply_markup=keyboard)

@Client.on_callback_query(filters.regex(r'^/changeMinMute'))
async def changeMinMuteDelayQuery(bot: Client,query: types.CallbackQuery):
    channelID = query.data.split(maxsplit=1)[1]
    await query.message.delete()
    await query.message.reply("<b>Send new minimum muting</b>",reply_markup=cancelKeyboard)
    minMute: str = (await bot.listen(query.message.chat.id)).text
    if minMute == cancelButtonText: 
        text , keyboard = await viewChannelActivity(int(channelID))
        return await query.message.reply(text=text,reply_markup=keyboard)
    elif not minMute.isdigit():
        await query.message.reply("<b>Invalid input, please try again</b>")
        return await changeMinMuteDelayQuery(bot,query)
    
    await query.message.reply("<b>Minimum muting updated successfully</b>")
    ActivityChannels.update_one(
        {"channelID":int(channelID)},
        {"$set":{"minimumMute":int(minMute)}}
    )
    text , keyboard = await viewChannelActivity(int(channelID))
    await query.message.reply(text=text,reply_markup=keyboard)

@Client.on_callback_query(filters.regex(r'^/changeMaxMute'))
async def changeMaxMuteDelayQuery(bot: Client,query: types.CallbackQuery):
    channelID = query.data.split(maxsplit=1)[1]
    await query.message.delete()
    await query.message.reply("<b>Send new maximum muting</b>",reply_markup=cancelKeyboard)
    maxMute: str = (await bot.listen(query.message.chat.id)).text
    if maxMute == cancelButtonText: 
        text , keyboard = await viewChannelActivity(int(channelID))
        return await query.message.reply(text=text,reply_markup=keyboard)
    elif not maxMute.isdigit():
        await query.message.reply("<b>Invalid input, please try again</b>")
        return await changeMaxMuteDelayQuery(bot,query)
    
    await query.message.reply("<b>Maximum muting updated successfully</b>")
    ActivityChannels.update_one(
        {"channelID":int(channelID)},
        {"$set":{"maximumMute":int(maxMute)}}
    )
    text , keyboard = await viewChannelActivity(int(channelID))
    await query.message.reply(text=text,reply_markup=keyboard)

@Client.on_callback_query(filters.regex(r'^/changeMinUnmute'))
async def changeMinUnmuteDelayQuery(bot: Client,query: types.CallbackQuery):
    channelID = query.data.split(maxsplit=1)[1]
    await query.message.delete()
    await query.message.reply("<b>Send new minimum unmute</b>",reply_markup=cancelKeyboard)
    minUnmute: str = (await bot.listen(query.message.chat.id)).text
    if minUnmute == cancelButtonText: 
        text , keyboard = await viewChannelActivity(int(channelID))
        return await query.message.reply(text=text,reply_markup=keyboard)
    elif not minUnmute.isdigit():
        await query.message.reply("<b>Invalid input, please try again</b>")
        return await changeMinUnmuteDelayQuery(bot,query)
    
    await query.message.reply("<b>Minimum unmute updated successfully</b>")
    ActivityChannels.update_one(
        {"channelID":int(channelID)},
        {"$set":{"minimumUnmute":int(minUnmute)}}
    )
    text , keyboard = await viewChannelActivity(int(channelID))
    await query.message.reply(text=text,reply_markup=keyboard)

@Client.on_callback_query(filters.regex(r'^/changeMaxUnmute'))
async def changeMaxUnmuteDelayQuery(bot: Client,query: types.CallbackQuery):
    channelID = query.data.split(maxsplit=1)[1]
    await query.message.delete()
    await query.message.reply("<b>Send new maximum unmute</b>",reply_markup=cancelKeyboard)
    maxUnmute: str = (await bot.listen(query.message.chat.id)).text
    if maxUnmute == cancelButtonText: 
        text , keyboard = await viewChannelActivity(int(channelID))
        return await query.message.reply(text=text,reply_markup=keyboard)
    elif not maxUnmute.isdigit():
        await query.message.reply("<b>Invalid input, please try again</b>")
        return await changeMaxUnmuteDelayQuery(bot,query)
    
    await query.message.reply("<b>Maximum unmute updated successfully</b>")
    ActivityChannels.update_one(
        {"channelID":int(channelID)},
        {"$set":{"maximumUnmute":int(maxUnmute)}}
    )
    text , keyboard = await viewChannelActivity(int(channelID))
    await query.message.reply(text=text,reply_markup=keyboard)



