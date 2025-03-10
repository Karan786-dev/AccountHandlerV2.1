from pyrogram import Client , filters , ContinuePropagation
from pyrogram.types import Message , InlineKeyboardMarkup , InlineKeyboardButton , CallbackQuery  , Chat , ReplyKeyboardRemove
from .responseFunctions import *
from config import *
from database import Accounts , Channels , Users
from datetime import datetime
from functions import *
from markups import *
from orderAccounts import UserbotManager
from pyrogram.errors import *
import re 
import asyncio

#Cancel Button 
@Client.on_message(filters.private)
async def backButton(_, msg):
    if msg.text != cancelButtonText: raise ContinuePropagation
    deleteResponse(msg.from_user.id)
    await msg.reply("You'r back !!!", reply_markup=ReplyKeyboardRemove())
    text, keyboard = mainMenu(msg.from_user)
    await msg.reply(text, reply_markup=keyboard)


#Function to broadcast
@Client.on_message(filters.private)
async def getBroadcastPost(_,message):
    if not checkIfTarget(message.from_user.id,"askForBroadcast"): raise ContinuePropagation()
    messageID = message.id 
    messageFrom = message.from_user.id
    usersData = list(Users.find({},{"userID":True}))
    canSendInOneSecond = 20
    sended = 0
    await message.reply("<b>Sending broadcast.......</b>")
    deleteResponse(messageFrom)
    for i in usersData:
        if canSendInOneSecond == sended:
            await asyncio.sleep(1)
            sended = 0
        sended += 1
        userID = i.get("userID")
        try:
            await _.copy_message(userID,messageFrom,messageID)
        except Exception as e:
            print(str(e))
    await message.reply(f"<b>Broadcast has been delivered to: </b><code>{len(usersData)} Users</code>")
    text, keyboard = adminPanel(message.from_user)
    await message.reply(text, reply_markup=keyboard)
    

# Fucntion to grant access to user
@Client.on_message(filters.private)
async def getUserIDToGrantAccess(_,message):
    if not checkIfTarget(message.from_user.id,"askUserIDForAccess"): raise ContinuePropagation()
    userID = message.text 
    if not is_number(userID):return await message.reply("<b>⚠️ Invalid input:  Please enter a valid value</b>")
    text ,keyboard = await grantAccessMarkup(int(userID))
    await message.reply(text,reply_markup=keyboard)


#Manually Change Duration of Voice Chat
@Client.on_message(filters.private)
async def manuallyChangeVoiceDuration(_,message:Message):
    if not checkIfTarget(message.from_user.id,"manuallyChangeVoiceDuration"): raise ContinuePropagation()
    if not is_number(message.text): return await message.reply("</b>🚫 Invalid Valid:</b> Make Sure To Enter Valid Integer")
    durationCountArray = message.text.split("-")
    responsesData = getResponse(message.from_user.id).get("payload")
    channelID = responsesData.get("channelID")
    Channels.update_one({"channelID":int(channelID)},{"$set":{"voiceDuration":durationCountArray}})
    text , keyboard = await manageChannelServices(channelID)
    await message.reply(text,reply_markup=keyboard)

#Manually Change Delay in Auto Services
@Client.on_message(filters.private)
async def manuallyChangeAutoServiceDelay(_,message:Message):
    if not checkIfTarget(message.from_user.id,"manuallyChangeAutoServiceDelay"): raise ContinuePropagation()
    delayCountArray = message.text.split("-")
    if not is_number(delayCountArray[0]) or (len(delayCountArray) == 2 and not is_number(delayCountArray[1])): return await message.reply("</b>🚫 Invalid Valid:</b> Make Sure To Enter Valid Integer")
    responsesData = getResponse(message.from_user.id).get("payload")
    channelID = responsesData.get("channelID")
    task = responsesData.get("task")
    if task == "views": query = {"$set":{"viewRestTime":delayCountArray}}
    elif task == "reactions": query = {"$set":{"reactionRestTime":delayCountArray}}
    elif task == "voice": query = {"$set": {"voiceRestTime":delayCountArray}}
    Channels.update_one({"channelID":int(channelID)},query)
    text , keyboard = await manageChannelServices(channelID)
    await message.reply(text,reply_markup=keyboard)
    
#Manually Change Count of Auto Services
@Client.on_message(filters.private)
async def manuallyChangeAutoServiceCount(_,message:Message):
    if not checkIfTarget(message.from_user.id,"manuallyChangeAutoServiceCount"): raise ContinuePropagation()
    delayCount = message.text
    if not is_number(delayCount): return await message.reply("</b>🚫 Invalid Valid:</b> Make Sure To Enter Valid Integer")
    responsesData = getResponse(message.from_user.id).get("payload")
    channelID = responsesData.get("channelID")
    task = responsesData.get("task")
    if task == "views": query = {"$set":{"viewCount":delayCount}}
    elif task == "reactions": query = {"$set":{"reactionsCount":delayCount}}
    elif task == "voice": query = {"$set": {"voiceCount":delayCount}}
    Channels.update_one({"channelID":int(channelID)},query)
    text , keyboard = await manageChannelServices(channelID)
    await message.reply(text,reply_markup=keyboard)

#Add a channel
@Client.on_message(filters.private)
async def getChannelID(_,message:Message):
    if not checkIfTarget(message.from_user.id,"addChannelLink"): raise ContinuePropagation()
    channelLink = message.text 
    deleteResponse(message.from_user.id)
    if (not channelLink.startswith('https://t.me/')) and (not channelLink.startswith("@")) : return await message.reply("<b>⚠️ Invalid input:  Please enter a valid value</b>")
    syncBotData = Accounts.find_one({"syncBot":True})
    waitingMsg = await message.reply("<b>SyncBot trying to join channel.......</b>")
    syncBot = UserbotManager.getSyncBotClient()
    if not syncBot: await _.edit_message_text(chat_id=message.from_user.id,message_id=waitingMsg.id,text=f"<b>⚠️ Failed To Join Channel</b>: Sync bot not found.")
    try:
        await syncBot.join_chat(channelLink)
    except Exception as e:
        if not "[400 USER_ALREADY_PARTICIPANT]" in str(e):
            await _.edit_message_text(chat_id=message.from_user.id,message_id=waitingMsg.id,text=f"<b>⚠️ Failed To Join Channel</b>: {str(e)}")
            raise e
    channelData = await syncBot.get_chat(channelLink)
    channelID = channelData.id
    if Channels.find_one({"channelID":channelID}): return await  _.edit_message_text(message.from_user.id,waitingMsg.id,"<b>⚠️ This Channel already exists in database</b>")
    # Check if the channel is public or private
    if channelData.username:channelType = "public" 
    else:channelType = "private"
    username = channelData.username or None 
    channelTitle = channelData.title
    Channels.insert_one({
        "channelID":channelID,
        "title": channelTitle,
        "username": username,
        "type": channelType,
        "inviteLink": channelLink if not channelLink.startswith("@") else channelLink.replace("@","https://t.me/")
    })
    await _.edit_message_text(chat_id=message.from_user.id,message_id=waitingMsg.id,text="<b>Channel Added Into Database</b>")
    text , keyboard = await viewChannelManage(channelID)
    await message.reply(text,reply_markup=keyboard)
    


#Dynamic Task Settings
@Client.on_callback_query(filters.regex(r'^/dynamicSpeed'))
async def dynamicSpeed(_,query:CallbackQuery):
    if not checkIfTarget(query.from_user.id,"dynamicSpeed"): raise ContinuePropagation()
    command , task , seconds = query.data.split(" ")
    responseData = getResponse(query.from_user.id).get("payload")
    if (not is_number(seconds)) or (float(seconds) < 0): return await query.message.reply("<b>⚠️ Invalid input:  Please enter a valid value</b>")
    userBots = list(Accounts.find({}))
    await query.message.edit("<b>📋 Executing The Task...</b>")
    if task == "views":
        count = responseData.get("numberOfViews")
        userBots = userBots[:int(random.choice(count if isinstance(count,list) else [count]))]
        await UserbotManager.bulk_order(userBots,{
            "type":"viewPosts",
            "postLink": responseData.get("postLink"),
            "restTime":float(seconds),
            "taskPerformCount": count
        })
    elif task == "reactions":
        count = responseData.get("numberOfReactions")
        userBots = userBots[:int(random.choice(count if isinstance(count,list) else [count]))]
        await UserbotManager.bulk_order(userBots,{
            "type":"reactPost",
            "postLink": responseData.get("postLink"),
            "restTime":float(seconds),
            "taskPerformCount":count,
            "emoji":responseData.get("emoji")
        })
        await UserbotManager.bulk_order(userBots,{
            "type":"viewPosts",
            "postLink": responseData.get("postLink"),
            "restTime":float(seconds),
            "taskPerformCount": count
        })
    elif task == "leaveChat":
        count = responseData.get("membersCount")
        userBots = userBots[:int(random.choice(count if isinstance(count,list) else [count]))]
        channelIDs = []
        for i in responseData.get("chatIDs"):
            if i.startswith('https://t.me/'):  
                channelData = await UserbotManager.getSyncBotClient().get_chat(i)
                channelIDs.append(channelData.id)
            else: channelIDs.append(i)
        await UserbotManager.bulk_order(userBots,{
            "type":"leave_channel",
            "channels": channelIDs,
            "restTime":float(seconds),
            "taskPerformCount": count
        })
    elif task == "joinChat":
        count = responseData.get("membersCount")
        userBots = userBots[:int(random.choice(count if isinstance(count,list) else [count]))]
        await UserbotManager.bulk_order(userBots,{
        "type":"join_channel",
        "channels": responseData.get("chatIDs"),
        "restTime":float(seconds),
        "taskPerformCount": count
        })
    elif task == "notify":
        createResponse(query.from_user.id,"askForNotifyChangeDuration",{**responseData,"speed":seconds})
        numberAllowed = [
            {"text": "Unmute", "value": 0},
            {"text": "1 Day", "value": 86400},
            {"text": "2 Days", "value": 172800},
            {"text": "5 Days", "value": 432000},
            {"text": "7 Days", "value": 604800},
            {"text": "10 Days", "value": 864000},
            {"text": "30 Days", "value": 2592000},
            {"text": "Forever", "value": 2147483647},
        ]
        buttons = InlineKeyboardMarkup(paginateArray([InlineKeyboardButton(i.get("text"),f"/notifyChangeDuration {i.get("value")}") for i in numberAllowed],3))
        return await query.message.edit("<b>Select the Mute Duration:</b>\n\nPlease choose the duration for muting the channel. You can select from the following options:\n<b>Alternatively</b>, you can choose Unmute to lift the mute and allow notifications from the channel again.",reply_markup=buttons)
    elif task == "report":
        count = responseData.get("reportsCount")
        userBots = userBots[:int(random.choice(count if isinstance(count,list) else [count]))]
        await UserbotManager.bulk_order(userBots,{
        "type":"reportChannel",
        "chatID": responseData.get("channelID"),
        "restTime":float(seconds),
        "taskPerformCount": count,
        "inviteLink":responseData.get("inviteLink")
        })
    elif task == "joinVoiceChat":
        count = responseData.get("membersCount")
        userBots = userBots[:int(random.choice(count if isinstance(count,list) else [count]))]
        await UserbotManager.bulk_order(userBots,{
        "type":"joinVoiceChat",
        "chatID": responseData.get("channelID"),
        "restTime":float(seconds),
        "taskPerformCount": count,
        "inviteLink":responseData.get("inviteLink")
        })
    elif task == "votePoll":
        count = responseData.get("numberOfVotes")
        userBots = userBots[:int(random.choice(count if isinstance(count,list) else [count]))]
        await UserbotManager.bulk_order(userBots,{
        "type":"votePoll",
        "chatID":responseData.get("chatID"),
        "messageID":responseData.get("messageID"),
        "optionIndex":responseData.get("optionIndex"),
        "restTime":float(seconds),
        "taskPerformCount": count,
        "inviteLink":responseData.get("inviteLink","")
        })
        await UserbotManager.bulk_order(userBots,{
            "type":"viewPosts",
            "postLink": responseData.get("postLink"),
            "restTime":float(seconds),
            "taskPerformCount": count
        })
    elif task == "sendMessage":
        count = responseData.get("messagesCount") 
        userBots = userBots[:int(random.choice(count if isinstance(count,list) else [count]))]
        shuffledArray = shuffleArray(userBots)
        msgSended = 0
        textArray = responseData.get("text")
        for i in shuffledArray:
            if len(textArray) == msgSended: msgSended = 0
            textToDeliver = textArray[msgSended]
            msgSended += 1
            await UserbotManager.add_task(i.get("phone_number"),{
            "type": "sendMessage",
            "chatID":responseData.get("chatID"),
            "text":textToDeliver,
            "restTime":float(seconds),
            "session_string": i["session_string"]
            })
    elif task == "sendPhoto":
        count = responseData.get("messagesCount") 
        userBots = userBots[:int(random.choice(count if isinstance(count,list) else [count]))]
        shuffledArray = shuffleArray(userBots)
        msgSended = 0
        photosSended = 0
        textArray = responseData.get("text")
        photosArray = responseData.get("photos")
        restTime = float(seconds)
        for i in shuffledArray:
            if len(textArray) == msgSended: msgSended = 0
            if len(photosArray) == photosSended: photosSended = 0
            photoToDeliver = photosArray[photosSended]
            textToDeliver = textArray[msgSended]
            msgSended += 1
            photosSended += 1
            if restTime > 0:
                print(f"Resting for {restTime} seconds before processing task for {i.get("phone_number")}")
                await asyncio.sleep(restTime)
            await UserbotManager.add_task(i.get("phone_number"),{
            "type": "sendPhoto",
            "chatID":responseData.get("chatID"),
            "photoLink":photoToDeliver,
            "restTime":restTime,
            "session_string": i["session_string"],
             })
            await UserbotManager.add_task(i.get("phone_number"),{
            "type": "sendMessage",
            "chatID":responseData.get("chatID"),
            "text":textToDeliver,
            "restTime":restTime,
            "session_string": i["session_string"],
            })
    await query.message.reply(f"<b>✅ Task Executed: {len(userBots)} Accounts</b>")

@Client.on_callback_query(filters.regex(r"^/dynamicQuantity"))
async def dynamicCountHandler(_,query:CallbackQuery):
    if not checkIfTarget(query.from_user.id,"dynamicCount"): raise ContinuePropagation()
    command , task , count = query.data.split(" ")
    responseData = getResponse(query.from_user.id).get("payload")
    if count == "Manual":
        createResponse(query.from_user.id,"manualWorkQuantity",{**responseData,"task":task})
        return await query.message.edit("<b>Send quantity of work\nRandom: </b>To Randomize quanitity separate minimum and maximum count with '-', like 4-10")
    if task == "notify": createResponse(query.from_user.id,"dynamicSpeed",{**responseData,"notifyChangeCount":int(count)})
    elif task == "report": createResponse(query.from_user.id,"dynamicSpeed",{**responseData,"reportsCount":int(count)})
    elif task == "voiceChat": createResponse(query.from_user.id,"dynamicSpeed",{**responseData,"membersCount":int(count)})
    elif task == "sendPhoto": createResponse(query.from_user.id,"dynamicSpeed",{**responseData,"messagesCount":int(count)})
    elif task == "reactions": createResponse(query.from_user.id,"dynamicSpeed",{**responseData,"numberOfReactions":int(count)})
    elif task == "votePoll": createResponse(query.from_user.id,"dynamicSpeed",{**responseData,"numberOfVotes":int(count)})
    elif task == "views": createResponse(query.from_user.id,"dynamicSpeed",{**responseData,"numberOfViews":int(count)})
    elif task == "leaveChat": createResponse(query.from_user.id,"dynamicSpeed",{**responseData,"membersCount":int(count)})
    elif task == "joinChat": createResponse(query.from_user.id,"dynamicSpeed",{**responseData,"membersCount":int(count)})
    elif task == "sendMessage": createResponse(query.from_user.id,"dynamicSpeed",{**responseData,"messagesCount":int(count)})
    text , keyboard = getAskSpeed(task=task)
    await query.message.edit(text,reply_markup=keyboard)


# Dynamic Manual Work Quantity
@Client.on_message(filters.private)
async def manuallyWorkQuantityHandler(_:Client,message:Message):
    if not checkIfTarget(message.from_user.id,"manualWorkQuantity"): raise ContinuePropagation()
    responseData = getResponse(message.from_user.id).get("payload")
    task = responseData.get("task",None)
    count = message.text.split("-")
    for i in count:
        if not is_number(i): return await message.reply("<b>Invalid: Please enter a valid integer amount</b>")
    if task == "notify": createResponse(message.from_user.id,"dynamicSpeed",{**responseData,"notifyChangeCount":count})
    elif task == "report": createResponse(message.from_user.id,"dynamicSpeed",{**responseData,"reportsCount":count})
    elif task == "voiceChat": createResponse(message.from_user.id,"dynamicSpeed",{**responseData,"membersCount":count})
    elif task == "sendPhoto": createResponse(message.from_user.id,"dynamicSpeed",{**responseData,"messagesCount":count})
    elif task == "reactions": createResponse(message.from_user.id,"dynamicSpeed",{**responseData,"numberOfReactions":count})
    elif task == "votePoll": createResponse(message.from_user.id,"dynamicSpeed",{**responseData,"numberOfVotes":count})
    elif task == "views": createResponse(message.from_user.id,"dynamicSpeed",{**responseData,"numberOfViews":count})
    elif task == "leaveChat": createResponse(message.from_user.id,"dynamicSpeed",{**responseData,"membersCount":count})
    elif task == "joinChat": createResponse(message.from_user.id,"dynamicSpeed",{**responseData,"membersCount":count})
    elif task == "sendMessage": createResponse(message.from_user.id,"dynamicSpeed",{**responseData,"messagesCount":count})
    text , keyboard = getAskSpeed(task=task)
    await message.reply(text,reply_markup=keyboard)

# Function to change Notification Of Channel
@Client.on_message(filters.private)
async def changeNotifyChannelGetIDHandler(_:Client,message:Message):
    if not checkIfTarget(message.from_user.id,"notifyChangeChatGetID"): raise ContinuePropagation()
    syncBot: Client = UserbotManager.getSyncBotClient()
    if not syncBot:return await query.message.reply("Syncbot not available")
    channelLink = message.text 
    if not channelLink.startswith("@"):
        channelInfo: Chat = None
        try:
            channelInfo = await syncBot.get_chat(channelLink)
        except PeerIdInvalid:
            print(f"SyncBot not a member of channel joining {channelLink}")
            channelInfo = await syncBot.join_chat(channelLink)
        channelID = channelInfo.id 
    else: channelID = channelLink
    deleteResponse(message.from_user.id)
    text , keyboard = getAskWorkQuantity(task="notify")
    await message.reply(text,reply_markup=keyboard)
    createResponse(message.from_user.id,"dynamicCount",{"channelID":channelID,"inviteLink":channelLink})

@Client.on_callback_query(filters.regex(r'^/notifyChangeDuration'))
async def notifyChangeDurationHandler(_:Client,query:CallbackQuery):
    if not checkIfTarget(query.from_user.id,"askForNotifyChangeDuration"): raise ContinuePropagation()
    duration = query.data.split(" ")[1]
    rawResponseData = getResponse(query.from_user.id)
    responseData = getResponse(query.from_user.id).get("payload")
    deleteResponse(query.from_user.id)
    userBots = shuffleArray(list(Accounts.find()))
    await query.message.edit("<b>📋 Executing The Task...</b>")
    await UserbotManager.bulk_order(userBots,{
        "type":"changeNotifyChannel",
        "chatID": responseData.get("channelID"),
        "restTime":responseData.get("speed"),
        "taskPerformCount": responseData.get("notifyChangeCount"),
        "inviteLink":responseData.get("inviteLink"),
        "duration": int(duration)
    })
    await query.message.reply(f"<b>✅ Task Executed: {len(userBots)} Accounts</b>")
    
    
# Function to join voice calls in channel
@Client.on_message(filters.private)
async def getChannelIDToJoinVoice(_,message):
    if not checkIfTarget(message.from_user.id,"joinVoiceChat"): raise ContinuePropagation()
    channelLink = message.text
    if not channelLink.startswith("@") and not channelLink.startswith("https://t.me/"): return await message.reply("<b>⚠️ Invalid input:  Please enter a valid value</b>")
    syncBot = UserbotManager.getSyncBotClient()
    try: 
        if not channelLink.startswith("@"): await syncBot.join_chat(channelLink)
    except Exception as e:
        if not "[400 USER_ALREADY_PARTICIPANT]" in str(e): return await message.reply(f"<b>⚠️ Failed To Join Channel</b>: {str(e)}")
        else:print(str(e))
    channelData = await syncBot.get_chat(channelLink)
    channelID = channelData.id if not channelLink.startswith("@") else channelLink
    await message.reply("<b>✅ SyncBot Joined The Channel Successfully</b>")
    text , keyboard = getAskWorkQuantity(task="notify")
    await message.reply(text,reply_markup=keyboard)
    deleteResponse(message.from_user.id)
    createResponse(message.from_user.id,"dynamicCount",{"channelID":channelID,"inviteLink":channelLink})
    
@Client.on_message(filters.private)
async def getChatIDTOReport(_,message:Message):
    if not checkIfTarget(message.from_user.id,"getChatIDToReport"): raise ContinuePropagation()
    channelLink = message.text
    if not channelLink.startswith("@") and not channelLink.startswith("https://t.me/"): return await message.reply("<b>⚠️ Invalid input:  Please enter a valid value</b>")
    syncBot = UserbotManager.getSyncBotClient()
    channelData = await syncBot.get_chat(channelLink)
    channelID = channelData.id if not channelLink.startswith("@") else channelLink
    await message.reply("<b>✅ SyncBot Joined The Channel Successfully</b>")
    text , keyboard = getAskWorkQuantity(task="report")
    await message.reply(text,reply_markup=keyboard)
    deleteResponse(message.from_user.id)
    createResponse(message.from_user.id,"dynamicCount",{"channelID":channelID,"inviteLink":channelLink})
    
#Function to get Photos
@Client.on_message(filters.private)
async def getPhotosToSent(_, message):
    if not checkIfTarget(message.from_user.id, "photosToSent"):
        raise ContinuePropagation()
    photos = message.photo
    if not photos:
        return await message.reply("<b>⚠️ Invalid input:  Please send a valid photo</b>")
    responseData = getResponse(message.from_user.id).get("payload", {})
    photosArray = responseData.get("photos", [])
    send_response = await _.send_photo(UPLOADING_CHANNEL, message.photo.file_id)
    post_link = f"https://t.me/{send_response.chat.username}/{send_response.id}"
    photosArray.append(post_link)
    await message.reply(
        f"<b>✅ Photo added to the list, Send another photo or Click 'Done'</b>",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Done", "/done")]])
    )
    deleteResponse(message.from_user.id)
    createResponse(message.from_user.id, "photosToSent", {"photos": photosArray})
    
@Client.on_callback_query(filters.regex(r'^/done'))
async def doneAddingPhotos(_,query):
    if not checkIfTarget(query.from_user.id,"photosToSent"): raise ContinuePropagation()
    photosArray = getResponse(query.from_user.id).get("payload").get("photos")
    deleteResponse(query.from_user.id)
    await query.message.reply(f"<b>✅ {len(photosArray)} Photos added to the list</b>")
    await query.message.edit(f"<b>📝 Enter The Message/Feedbacks (separate them with '|')</b>",reply_markup=cancelKeyboard)
    createResponse(query.from_user.id,"messageWithPhotos",{"photos":photosArray})

@Client.on_message(filters.private)
async def getMessageToSendWithPhotoHandler(_,message):
    if not checkIfTarget(message.from_user.id,"messageWithPhotos"): raise ContinuePropagation()
    try:
        text = str(message.text)
        textArray = text.split("|") if "|" in text else [text]
        photosArray = getResponse(message.from_user.id).get("payload").get("photos")
        await message.reply("📩 Send the username of the person you want to send.")
        deleteResponse(message.from_user.id)
        createResponse(message.from_user.id,"sendPhotoWithMessageChatID",{"text":textArray,"photos":photosArray})
    except Exception as e:
        raise e

@Client.on_message(filters.private)
async def getMessageDeliverIDWithPhotoHandler(_,message):
    if not checkIfTarget(message.from_user.id,"sendPhotoWithMessageChatID"): raise ContinuePropagation
    responseData = getResponse(message.from_user.id).get("payload")
    chatID = message.text 
    deleteResponse(message.from_user.id)
    createResponse(message.from_user.id,"dynamicCount",{**responseData,"chatID":chatID})
    text , keyboard = getAskWorkQuantity(task="sendPhoto")
    await message.reply(text,reply_markup=keyboard)

# Function to vote in a pool
@Client.on_message(filters.private)
async def getPostLinkToVote(_,message:Message):
    if not checkIfTarget(message.from_user.id,"postLinkToVote"): raise ContinuePropagation()
    postLink = str(message.text).replace("/c","")
    responsesData = getResponse(message.from_user.id).get("payload",{})
    match = re.match(r"https://t.me/(?P<chat>[\w_]+)/(?P<msg_id>\d+)", postLink)
    deleteResponse(message.from_user.id)
    if not match: return await message.reply("<b>⚠️ Invalid input:  Please enter a valid url</b>")
    try:
        chat = match.group("chat")
        chatID = int("-100"+chat) if is_number(chat) else chat
        msg_id = int(match.group("msg_id"))
        if is_number(chat) and not responsesData.get("inviteLink"):
            await message.reply(
                f"<b>🔒 It appears the channel is private"
                f"Please send the channel's invite link</b>"
            )
            return createResponse(message.from_user.id,"inviteLinkToVotePoll")
        syncBot = UserbotManager.getSyncBotClient()
        messageData = await syncBot.get_messages(chatID, msg_id)
        if not messageData.poll: return await message.reply("<b>⚠️ This message does not contain a poll</b>")
        pollData = messageData.poll
        text = (
            "<b>Choose An Option From Below To Vote</b>\n"
            f"<b>Question:\t\t</b>{pollData.question}\n"
        )
        options = pollData.options
        buttons = InlineKeyboardMarkup(paginateArray([InlineKeyboardButton(options[i].text,f"/vote {i}") for i in range(len(options))],2))
        await message.reply(text,reply_markup=buttons)
        deleteResponse(message.from_user.id)
        createResponse(message.from_user.id,"voteOnPollCallback",{
            "chatID":chatID,
            "messageID": msg_id,
            "inviteLink":responsesData.get("inviteLink",""),
            "postLink": message.text
        })
    except Exception as e:
        print(e)
            
@Client.on_callback_query(filters.regex(r'^/vote'))
async def voteOnPollCallback(_,query:CallbackQuery):
    if not checkIfTarget(query.from_user.id,"voteOnPollCallback"): raise ContinuePropagation()
    responseData = getResponse(query.from_user.id).get("payload")
    optionIndex = int(query.data.split(maxsplit=1)[1])
    text , keyboard = getAskWorkQuantity(task="votePoll")
    await query.message.edit(text,reply_markup=keyboard)
    deleteResponse(query.from_user.id)
    createResponse(query.from_user.id,"dynamicCount",{**responseData,"optionIndex":optionIndex})


@Client.on_message(filters.private) 
async def getInviteLinkToAddSyncBot(_,message):
    if not checkIfTarget(message.from_user.id,"inviteLinkToVotePoll"): raise ContinuePropagation()
    inviteLink = message.text
    if not inviteLink.startswith('https://t.me/'): return await message.reply("<b>⚠️ Invalid input:  Please enter a valid url</b>")
    syncBot = UserbotManager.getSyncBotClient()
    try:
        await syncBot.join_chat(inviteLink)
    except Exception as e:
        if not "[400 USER_ALREADY_PARTICIPANT]" in str(e): return await message.reply(f"<b>⚠️ Failed To Join Channel</b>: {str(e)}\nPlease Try Again")
    await message.reply("<b>✅ SyncBot Joined The Channel Successfully</b>",)
    deleteResponse(message.from_user.id)
    await message.reply("<b>📨 Please provide the post link to proceed with sending votes. 📬</b>",reply_markup=cancelKeyboard)
    createResponse(message.from_user.id,"postLinkToVote",{"inviteLink":inviteLink})
    

#Functions to send reactions
@Client.on_message(filters.private)
async def getPostLinkToReact(_,message):
    if not checkIfTarget(message.from_user.id,"postLinkTosendReaction"): raise ContinuePropagation()
    postLink = str(message.text).replace("/c","")
    if not postLink.startswith('https://'): return await message.reply("<b>⚠️ Invalid input:  Please enter a valid url</b>")
    deleteResponse(message.from_user.id)
    await message.reply("<b>👀 Enter Emoji to React:</b>")
    createResponse(message.from_user.id,"emojiToSendReaction",{"postLink":postLink})
    
@Client.on_message(filters.private)
async def getEmojiToReact(_,message):
    if not checkIfTarget(message.from_user.id,"emojiToSendReaction"): raise ContinuePropagation()
    responseData = getResponse(message.from_user.id).get("payload")
    if not message.text: raise ContinuePropagation()
    emojiToReact = message.text.split(",") 
    deleteResponse(message.from_user.id)
    text , keyboard = getAskWorkQuantity(task="reactions")
    await message.reply(text,reply_markup=keyboard)
    createResponse(message.from_user.id,"dynamicCount",{**responseData,"emoji":emojiToReact})

#Function to send views
@Client.on_message(filters.private)
async def getPostLinkToSendViews(_,message):
    if not checkIfTarget(message.from_user.id,"postLinkTosendViews"): raise ContinuePropagation()
    postLink = str(message.text).replace("/c","")
    if not postLink.startswith('https://'): return await message.reply("<b>⚠️ Invalid input:  Please enter a valid url</b>")
    deleteResponse(message.from_user.id)
    text , keyboard = getAskWorkQuantity(task="views")
    await message.reply(text,reply_markup=keyboard)
    createResponse(message.from_user.id,"dynamicCount",{"postLink":postLink})


#Leave Channels Functions
@Client.on_message(filters.private)
async def getChatIDtoleave(_,message):
    if not checkIfTarget(message.from_user.id,"leaveChatID"): raise ContinuePropagation()
    chatID = message.text 
    chatIDArray = chatID.split("|")
    deleteResponse(message.from_user.id)
    text , keyboard = getAskWorkQuantity(task="leaveChat")
    await message.reply(text,reply_markup=keyboard)
    createResponse(message.from_user.id,"dynamicCount",{"chatIDs":chatIDArray})

    

#Join Channel Functions
@Client.on_message(filters.private)
async def getChatIDtoJoin(_,message):
    if not checkIfTarget(message.from_user.id,"joinChatID"): raise ContinuePropagation()
    chatID = message.text 
    chatIDArray = chatID.split("|")
    deleteResponse(message.from_user.id)
    text , keyboard = getAskWorkQuantity(task="joinChat")
    await message.reply(text,reply_markup=keyboard)
    createResponse(message.from_user.id,"dynamicCount",{"chatIDs":chatIDArray})


@Client.on_message(filters.private)
async def getMessageToSendHandler(_,message):
    if not checkIfTarget(message.from_user.id,"messageToSend"): raise ContinuePropagation()
    try:
        text = str(message.text)
        textArray = text.split("|") if "|" in text else [text]
        deleteResponse(message.from_user.id)
        await message.reply("📩 Send the username of the person you want to send messages.")
        createResponse(message.from_user.id,"messageDeliverChatID",{"text":textArray})
    except Exception as e:
        raise e
    
@Client.on_message(filters.private)
async def getMessageDeliverIDHandler(_,message):
    if not checkIfTarget(message.from_user.id,"messageDeliverChatID"): raise ContinuePropagation
    responseData = getResponse(message.from_user.id).get("payload")
    chatID = message.text 
    deleteResponse(message.from_user.id)
    createResponse(message.from_user.id,"dynamicCount",{**responseData,"chatID":chatID})
    text , keyboard = getAskWorkQuantity(task="sendMessage")
    await message.reply(text,reply_markup=keyboard)
    

@Client.on_message(filters.private)
async def createUserbotPhoneNumber(client, message):
    if not checkIfTarget(message.from_user.id, "createBot_phoneNumber"):
        raise ContinuePropagation
    phone_number = message.text
    oldAccountData = Accounts.find_one({"phone_number": phone_number})
    if oldAccountData:
        return await message.reply("<b>This account already exists in bot. Try sending another one</b>")
    deleteResponse(message.from_user.id)
    userbotClient = Client(USERBOT_SESSION+"/"+phone_number,API_ID,API_HASH)
    try:
        await userbotClient.connect()
        send_code = await userbotClient.send_code(phone_number=phone_number)
        await message.reply("<b>✅ Code Sent Successfully, Enter Your Code</b>")
        createResponse(message.from_user.id, "createUserbot_code", {"phone_number": phone_number, "phone_code_hash": send_code.phone_code_hash,"client":userbotClient})
    except Exception as e:
        await message.reply(f"<b>Failed to Connect: {e}</b>", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Try again!!", "addUserbot")]]))

@Client.on_message(filters.private)
async def createUserbotCode(client, message):
    if not checkIfTarget(message.from_user.id, "createUserbot_code"):
        raise ContinuePropagation
    phone_number = getResponse(message.from_user.id)["payload"]["phone_number"]
    phone_code_hash = getResponse(message.from_user.id)["payload"]["phone_code_hash"]
    userbotClient = getResponse(message.from_user.id)["payload"]["client"]
    code = message.text
    try:
        await userbotClient.sign_in(phone_number=phone_number,phone_code=code,phone_code_hash=phone_code_hash)
        sessionString = await client.export_session_string()
        deleteResponse(message.from_user.id)
        await message.reply("<b>✅ Account Authenticated Successfully</b>",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Add Another","/add_account")]]))
        botInfoFromTg = await userbotClient.get_me()
        accountData = {
            "phone_number": phone_number,
            "added_at": datetime.now(),
            "session_string": sessionString,
        }
        accountData["username"] = botInfoFromTg.username if botInfoFromTg.username else None
        Accounts.insert_one(accountData)
        await userbotClient.disconnect()
        accountDetails = Accounts.find_one({"phone_number": phone_number})
        text, keyboard = await account_details_view(accountDetails)
        await message.reply(text, reply_markup=keyboard)
    except PhoneCodeInvalid:
        await message.reply("<b>⚠️ Invalid Code:  Please enter a valid code</b>")
    except PhoneCodeExpired:
        await message.reply("<b>⚠️ Code Expired:  Please try again</b>")
    except SessionPasswordNeeded:
        await message.reply("<b>⚠️ 2FA Password Needed:  Please enter the 2FA Password</b>")
        createResponse(message.from_user.id, "createUserbot_password", {**getResponse(message.from_user.id)["payload"],})
    except Exception as e:
        await message.reply(f"<b>Failed to Connect: {e}</b>", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Try again!!", "addUserbot")]]))
        raise e
    
@Client.on_message(filters.private)
async def createUserbotPassword(client, message):
    if not checkIfTarget(message.from_user.id, "createUserbot_password"):
        raise ContinuePropagation
    phone_number = getResponse(message.from_user.id)["payload"]["phone_number"]
    phone_code_hash = getResponse(message.from_user.id)["payload"]["phone_code_hash"]
    password = message.text
    try:
        userbotClient = getResponse(message.from_user.id)["payload"]["client"]
        await userbotClient.check_password(password)
        sessionString = await userbotClient.export_session_string()
        deleteResponse(message.from_user.id)
        await message.reply("<b>✅ Account Authenticated Successfully</b>",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Add Another","/add_account")]]))
        botInfoFromTg = await userbotClient.get_me()
        accountData = {
            "phone_number": phone_number,
            "added_at": datetime.now(),
            "session_string": sessionString,
            "password": password,
        }
        accountData["username"] = botInfoFromTg.username if botInfoFromTg.username else None
        Accounts.insert_one(accountData)
        await userbotClient.disconnect()
        accountDetails = Accounts.find_one({"phone_number": phone_number})
        text, keyboard = await account_details_view(accountDetails)
        await message.reply(text, reply_markup=keyboard)
    except Exception as e:
        await message.reply(f"<b>Failed to Sign In: {e}</b>", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Try again!!", "addUserbot")]]))
        raise e
    