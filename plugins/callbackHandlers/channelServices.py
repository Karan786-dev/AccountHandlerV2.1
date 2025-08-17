from pyrogram import Client , filters  
from pyrogram.types import CallbackQuery , InlineKeyboardButton , InlineKeyboardMarkup
from functions import *
from markups import *
from database import Channels
from ..responses.responseFunctions import *
from config import cancelKeyboard


@Client.on_callback_query(filters.regex(r'^/channelServices'))
async def manageChannelServicesHandler(_,query:CallbackQuery):
    channelID = query.data.split(maxsplit=1)[1]
    text , keyboard = await manageChannelServices(int(channelID))
    await query.message.edit(text,reply_markup=keyboard)
    

@Client.on_callback_query(filters.regex(r'^/changeVoiceDuration'))
async def changeVoiceDurationHandler(_:Client,query:CallbackQuery):
    channelID = int(query.data.split(maxsplit=1)[1])
    numberAllowed = [1,5,10,20,30,40,50,100,300,"Manual"]
    buttons = InlineKeyboardMarkup(paginateArray([InlineKeyboardButton(str(i),f"/VoiceConfirmDuration {i} {channelID}") for i in numberAllowed],3))
    await query.message.edit("<b>👀 Select The Duration of Voice Chat:</b>",reply_markup=buttons)
    
@Client.on_callback_query(filters.regex(r'^/VoiceConfirmDuration'))
async def changeVoiceDurationConfirm(_:Client,query:CallbackQuery):
    param = query.data.split(maxsplit=1)[1].split()
    count = param[0]
    channelID = int(param[1])
    if count == 'Manual': 
        await query.message.delete()
        await query.message.reply("<b>Please enter the duration of voice chat in seconds</b>\n\n<b>Random</b>: To Randomize the duration enter minimum and maximum delay like 1-10",reply_markup=cancelKeyboard)
        return createResponse(query.from_user.id,"manuallyChangeVoiceDuration",{"channelID":channelID})
    Channels.update_one({"channelID":channelID},{"$set":{"voiceDuration":[int(count)]}})
    text , keyboard = await manageChannelServices(channelID)
    await query.message.edit(text,reply_markup=keyboard)
   
@Client.on_callback_query(filters.regex(r'^/toggle_booster'))
async def toggleBoosterHandler(_,query:CallbackQuery):
    channelID = int(query.data.split(maxsplit=1)[1])
    channelData = Channels.find_one({"channelID":int(channelID)})
    isEnabled = channelData.get('isBoosterEnabled',False)
    if isEnabled: Channels.update_one({"channelID":channelID},{"$unset":{"isBoosterEnabled":True}})
    else: Channels.update_one({"channelID":channelID},{"$set":{"isBoosterEnabled":True}})
    text , keyboard = await manageChannelServices(channelID)
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
async def changeVoiceCountHandler(_:Client,query:CallbackQuery):
    param = query.data.split(maxsplit=1)[1].split()
    count = param[0]
    channelID = int(param[1])
    if count == 'Manual': 
        await query.message.delete()
        await query.message.reply("<b>Please enter count of work</b>",reply_markup=cancelKeyboard)
        return createResponse(query.from_user.id,"manuallyChangeAutoServiceCount",{"task":"voice","channelID":channelID})
    Channels.update_one({"channelID":channelID},{"$set":{"voiceCount":int(count)}})
    text , keyboard = await manageChannelServices(channelID)
    await query.message.edit(text,reply_markup=keyboard)

@Client.on_callback_query(filters.regex(r'^/changeViewsCount'))
async def changeViewsCount(_,query:CallbackQuery):
    param = query.data.split(maxsplit=1)[1].split()
    count = param[0]
    channelID = int(param[1])
    if count == 'Manual': 
        await query.message.delete()
        await query.message.reply("<b>Please enter count of work</b>",reply_markup=cancelKeyboard)
        return createResponse(query.from_user.id,"manuallyChangeAutoServiceCount",{"task":"views","channelID":channelID})
    Channels.update_one({"channelID":channelID},{"$set":{"viewCount":int(count)}})
    text , keyboard = await manageChannelServices(channelID)
    await query.message.edit(text,reply_markup=keyboard)
    
@Client.on_callback_query(filters.regex(r'^/changeReactionCount'))
async def changeReactionCount(_,query:CallbackQuery):
    param = query.data.split(maxsplit=1)[1].split()
    count = param[0]
    channelID = int(param[1])
    if count == 'Manual': 
        await query.message.delete()
        await query.message.reply("<b>Please enter count of work</b>",reply_markup=cancelKeyboard)
        return createResponse(query.from_user.id,"manuallyChangeAutoServiceCount",{"task":"reactions","channelID":channelID})
    Channels.update_one({"channelID":channelID},{"$set":{"reactionsCount":int(count)}})
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
        await query.message.delete()
        await query.message.reply("<b>Please type delay between work</b>\n\n<b>Random</b>: To Randomize the delay enter minimum and maximum delay like 1-10",reply_markup=cancelKeyboard)
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
        await query.message.delete()
        await query.message.reply("<b>Please type delay between work</b>\n\n<b>Random</b>: To Randomize the delay enter minimum and maximum delay like 1-10",reply_markup=cancelKeyboard)
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
        await query.message.delete()
        await query.message.reply("<b>Please type delay between work</b>\n\n<b>Random</b>: To Randomize the delay enter minimum and maximum delay like 1-10",reply_markup=cancelKeyboard)
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
    
@Client.on_callback_query(filters.regex(r'^/autoVotes'))
async def autoVotesSet(_:Client,query:CallbackQuery):
    channelID = int(query.data.split(maxsplit=1)[1])
    
    text , keyboard = await getAutoVotesMarkup(channelID)
    await query.message.edit(text,reply_markup=keyboard)
 
@Client.on_callback_query(filters.regex(r'^/setVotePercentage'))
async def setVotePercentage(_: Client,query: CallbackQuery):
    param = query.data.split(maxsplit=1)[1].split()
    channelID = param[0]
    option = param[1]
    
    channelData = Channels.find_one({"channelID": int(channelID)})
    
    if not channelData: await query.answer("Chal bkl :)")
    
    await query.message.edit(f"<b>Send new percentage for option {int(option) + 1}:</b>")
    createResponse(query.from_user.id,"optionPercentage",{"channelID": channelID, "option": option})
    
    
@Client.on_callback_query(filters.regex(r'^/setVoteCount'))
async def setVoteCountQuery(_: Client,query: CallbackQuery):
    channelID = int(query.data.split(maxsplit=1)[1])
    channelData = Channels.find_one({"channelID": int(channelID)})
    tryAgainButton = InlineKeyboardMarkup([[InlineKeyboardButton("Try Again", callback_data=f"/setVoteCount {channelID}")]])
    if not channelData: await query.answer("Chal bkl :)")
    await query.message.edit("<b>Send new count of votes\n</b><code></code>Note: You can separate minimum and maximum votes with a dash like 100-200</code>", reply_markup=tryAgainButton)
    answer = (await _.wait_for_message(query.from_user.id, filters.text)).text.strip().split("-")
    if not is_number(answer[0]):return await query.message.reply("<b>Invalid count, please try again.</b>", reply_markup=tryAgainButton)
    if len(answer) > 1 and not is_number(answer[1]): return await query.message.reply("<b>Invalid count, please try again.</b>", reply_markup=tryAgainButton)
    Channels.update_one({"channelID": int(channelID)}, {"$set": {"votesCount": answer[0] if len(answer) == 1 else answer}})
    text , keyboard = await getAutoVotesMarkup(channelID)
    await query.message.reply(text, reply_markup=keyboard)
    
@Client.on_callback_query(filters.regex(r'^/setVoteDelay'))
async def setVoteDelayQuery(_: Client,query: CallbackQuery):
    channelID = int(query.data.split(maxsplit=1)[1])
    channelData = Channels.find_one({"channelID": int(channelID)})
    tryAgainButton = InlineKeyboardMarkup([[InlineKeyboardButton("Try Again", callback_data=f"/setVoteDelay {channelID}")]])
    if not channelData: await query.answer("Chal bkl :)")
    backButton = InlineKeyboardMarkup([[InlineKeyboardButton("<- Back", callback_data=f"/autoVotes {channelID}")]])
    await query.message.edit("<b>Send new delay for votes\n</b><code></code>Note: You can separate minimum and maximum delay with a dash like 100-200 or use 0 for instant votes</code>", reply_markup=backButton)
    answerMsg = (await _.wait_for_message(query.from_user.id, filters.text))
    answer = answerMsg.text.strip().split("-")
    if not is_number(answer[0]):return await answerMsg.reply_text("<b>Invalid delay, please try again.</b>", reply_markup=tryAgainButton)
    if len(answer) > 1 and not is_number(answer[1]): return await answerMsg.reply_text("<b>Invalid delay, please try again.</b>", reply_markup=tryAgainButton)
    Channels.update_one({"channelID": int(channelID)}, {"$set": {"voteRestTime": answer[0] if len(answer) == 1 else answer}})
    text , keyboard = await getAutoVotesMarkup(channelID)
    await query.message.reply(text, reply_markup=keyboard)
    
@Client.on_callback_query(filters.regex(r'^/toggleAutoVote'))
async def toggleAutoVoteQuery(_: Client,query: CallbackQuery):
    channelID = int(query.data.split(maxsplit=1)[1])
    channelData = Channels.find_one({"channelID": int(channelID)})
    isEnabled = channelData.get("isVoteEnabled", False)
    if isEnabled:
        Channels.update_one({"channelID": int(channelID)}, {"$unset": {"isVoteEnabled": True}})
        
    else:
        Channels.update_one({"channelID": int(channelID)}, {"$set": {"isVoteEnabled": True},"$push": {"services": "auto_votes"}})
    
    text , keyboard = await getAutoVotesMarkup(channelID)
    await query.message.edit(text, reply_markup=keyboard)
    
    