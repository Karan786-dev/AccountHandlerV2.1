from pyrogram import Client , filters  
from pyrogram.types import CallbackQuery , InlineKeyboardButton , InlineKeyboardMarkup
from functions import *
from markups import *
from database import Channels
from ..responses.responseFunctions import *


@Client.on_callback_query(filters.regex(r'^/channelServices'))
async def manageChannelServicesHandler(_,query:CallbackQuery):
    channelID = query.data.split(maxsplit=1)[1]
    text , keyboard = await manageChannelServices(int(channelID))
    await query.message.edit(text,reply_markup=keyboard)
    
    
   
@Client.on_callback_query(filters.regex(r'^/toggle_voice'))
async def toggleVoiceChatHandler(_,query:CallbackQuery):
    channelID = int(query.data.split(maxsplit=1)[1])
    channelData = Channels.find_one({"channelID":int(channelID)})
    isEnabled = channelData.get("isVoiceEnabled",False)
    if isEnabled: Channels.update_one({"channelID":channelID},{"$unset":{"isVoiceEnabled":True},"$pull":{"services":"voice_chat"}})
    else: Channels.update_one({"channelID":channelID},{"$set":{"isVoiceEnabled":True},"$push":{"services":"voice_chat"}})
    text , keyboard = await manageChannelServices(channelID)
    await query.message.edit(text,reply_markup=keyboard)

@Client.on_callback_query(filters.regex(r'^/toggle_views'))
async def toggleViewsHandler(_,query:CallbackQuery):
    channelID = int(query.data.split(maxsplit=1)[1])
    channelData = Channels.find_one({"channelID":int(channelID)})
    isEnabled = channelData.get('isViewEnabled',False)
    if isEnabled: Channels.update_one({"channelID":channelID},{"$unset":{"isViewEnabled":True},"$pull":{"services":"view_posts"}})
    else: Channels.update_one({"channelID":channelID},{"$set":{"isViewEnabled":True},"$push":{"services":"view_posts"}})
    text , keyboard = await manageChannelServices(channelID)
    await query.message.edit(text,reply_markup=keyboard)
    
@Client.on_callback_query(filters.regex(r'^/toggle_reactions'))
async def toggleReactionsHandler(_,query:CallbackQuery):
    channelID = int(query.data.split(maxsplit=1)[1])
    channelData = Channels.find_one({"channelID":int(channelID)})
    isEnabled = channelData.get('isReactionsEnabled',False)
    if isEnabled: Channels.update_one({"channelID":channelID},{"$unset":{"isReactionsEnabled":True},"$pull":{"services":"reaction_posts"}})
    else: Channels.update_one({"channelID":channelID},{"$set":{"isReactionsEnabled":True},"$push":{"services":"reaction_posts"}})
    text , keyboard = await manageChannelServices(channelID)
    await query.message.edit(text,reply_markup=keyboard)

    
@Client.on_callback_query(filters.regex(r'^/changeCount'))
async def changeCountofTask(_,query:CallbackQuery):
    param = query.data.split(maxsplit=1)[1].split()
    task = param[0]
    channelID = int(param[1])
    numberAllowed = [1,5,10,20,30,40,50,100,300,"Manual"]
    if task == "views": command = "/changeViewsCount"
    elif task == "reactions": command = "/changeReactionCount"
    elif task == "voice": command = "/changeVoiceCount"
    else: return await query.answer("Task not found.")
    buttons = InlineKeyboardMarkup(paginateArray([InlineKeyboardButton(str(i),f"{command} {i} {channelID}") for i in numberAllowed],3))
    await query.message.edit("<b>👀 Select The Count:</b>",reply_markup=buttons)
    
@Client.on_callback_query(filters.regex(r'^/changeVoiceCount'))
async def changeVoiceCount(_:Client,query:CallbackQuery):
    param = query.data.split(maxsplit=1)[1].split()
    count = int(param[0])
    channelID = int(param[1])
    if count == 'Manual': 
        await query.message.reply("<b>Please enter count of work</b>")
        return createResponse(query.from_user.id,"manuallyChangeAutoServiceCount",{"task":"voice","channelID":channelID})
    Channels.update_one({"channelID":channelID},{"$set":{"voiceCount":count}})
    text , keyboard = await manageChannelServices(channelID)
    await query.message.edit(text,reply_markup=keyboard)

@Client.on_callback_query(filters.regex(r'^/changeViewsCount'))
async def changeViewsCount(_,query:CallbackQuery):
    param = query.data.split(maxsplit=1)[1].split()
    count = int(param[0])
    channelID = int(param[1])
    if count == 'Manual': 
        await query.message.reply("<b>Please enter count of work</b>")
        return createResponse(query.from_user.id,"manuallyChangeAutoServiceCount",{"task":"views","channelID":channelID})
    Channels.update_one({"channelID":channelID},{"$set":{"viewCount":count}})
    text , keyboard = await manageChannelServices(channelID)
    await query.message.edit(text,reply_markup=keyboard)
    
@Client.on_callback_query(filters.regex(r'^/changeReactionCount'))
async def changeReactionCount(_,query:CallbackQuery):
    param = query.data.split(maxsplit=1)[1].split()
    count = int(param[0])
    channelID = int(param[1])
    if count == 'Manual': 
        await query.message.reply("<b>Please enter count of work</b>")
        return createResponse(query.from_user.id,"manuallyChangeAutoServiceCount",{"task":"reactions","channelID":channelID})
    Channels.update_one({"channelID":channelID},{"$set":{"reactionsCount":count}})
    text , keyboard = await manageChannelServices(channelID)
    await query.message.edit(text,reply_markup=keyboard)

@Client.on_callback_query(filters.regex(r'^/changeDelay'))
async def changeDelayTime(_,query:CallbackQuery):
    param = query.data.split(maxsplit=1)[1].split()
    task = param[0]
    channelID = int(param[1])
    numberAllowed = [0,1,5,10,25,50,60,120,300,"Manual"]
    if task == "views": command = "/changeViewsDelayConfirm"
    elif task == "reactions": command = "/changeReactionsDelayConfirm"
    elif task == "voice": command = "/changeVoiceDelayConfirm"
    else: return await query.answer("Task not found.")
    buttons = InlineKeyboardMarkup(paginateArray([InlineKeyboardButton(str(i) if (i != 0) else "Instant",f"{command} {i} {channelID}") for i in numberAllowed],3))
    await query.message.edit(
        "<b>⚡️ Select The Delay Between Work Of The Work: ( In Seconds )</b>\n"
        "Instant = All Comes in Instantly.\n"
        "1 = 1 Account Per Seconds\n"
        "60 = 1 Account Per Minute",
        reply_markup=buttons
    )
    
@Client.on_callback_query(filters.regex(r'^/changeVoiceDelayConfirm'))
async def changeVoiceDelay(_:Client,query:CallbackQuery):
    param = query.data.split(maxsplit=1)[1].split()
    delay = param[0]
    channelID = int(param[1])
    if delay == 'Manual': 
        await query.message.reply("<b>Please type delay between work</b>\n\n<b>Random</b>: To Randomize the delay enter minimum and maximum delay like 1-10")
        return createResponse(query.from_user.id,"manuallyChangeAutoServiceDelay",{"task":"voice","channelID":channelID})
    delay = int(delay)
    Channels.update_one({"channelID":channelID},{"$set":{"voiceRestTime":[delay]}})
    text , keyboard = await manageChannelServices(channelID)
    await query.message.edit(text,reply_markup=keyboard)
    
@Client.on_callback_query(filters.regex(r'^/changeViewsDelayConfirm'))
async def changeViewsDelay(_,query:CallbackQuery):
    param = query.data.split(maxsplit=1)[1].split()
    delay = param[0]
    channelID = int(param[1])
    if delay == 'Manual': 
        await query.message.reply("<b>Please type delay between work</b>\n\n<b>Random</b>: To Randomize the delay enter minimum and maximum delay like 1-10")
        return createResponse(query.from_user.id,"manuallyChangeAutoServiceDelay",{"task":"views","channelID":channelID})
    delay = int(delay)
    Channels.update_one({"channelID":channelID},{"$set":{"viewRestTime":[delay]}})
    text , keyboard = await manageChannelServices(channelID)
    await query.message.edit(text,reply_markup=keyboard)
    
@Client.on_callback_query(filters.regex(r'^/changeReactionsDelayConfirm'))
async def changeReactionsDelay(_,query:CallbackQuery):
    param = query.data.split(maxsplit=1)[1].split()
    delay = param[0]
    channelID = int(param[1])
    if delay == 'Manual': 
        await query.message.reply("<b>Please type delay between work</b>\n\n<b>Random</b>: To Randomize the delay enter minimum and maximum delay like 1-10")
        return createResponse(query.from_user.id,"manuallyChangeAutoServiceDelay",{"task":"reactions","channelID":channelID})
    delay = int(param[0])
    Channels.update_one({"channelID":channelID},{"$set":{"reactionRestTime":delay}})
    text , keyboard = await manageChannelServices(channelID)
    await query.message.edit(text,reply_markup=keyboard)
    
@Client.on_callback_query(filters.regex(r'^/reactionEmoji'))
async def changeReactionOnChannel(_,query:CallbackQuery):
    channelID = int(query.data.split(maxsplit=1)[1])
    text , keyboard = await selectReactionEmoji(channelID)
    await query.message.edit(text,reply_markup=keyboard)
    

@Client.on_callback_query(filters.regex(r'^/toggleEmoji'))
async def toggleEmojiHandler(_,query:CallbackQuery):
    param = query.data.split(maxsplit=1)[1].split()
    emoji = param[0]
    channelID = int(param[1])
    channelData = Channels.find_one({"channelID":channelID})
    added_emojis = channelData.get("reactionsType", [])
    if emoji in added_emojis: Channels.update_one({"channelID":channelID},{"$pull":{"reactionsType":emoji}})
    else: Channels.update_one({"channelID":channelID},{"$push":{"reactionsType":emoji}})
    text , keyboard = await selectReactionEmoji(channelID)
    await query.message.edit(text,reply_markup=keyboard)
    
 