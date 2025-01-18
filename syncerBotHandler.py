from pyrogram import Client , filters , types
from pyrogram.types import Message 
from pyrogram.raw.types import UpdateGroupCall , GroupCallDiscarded
from database import Channels , Accounts
from orderAccounts import UserbotManager
import random

async def messageHandler(_,message:Message):
    channelID = message.chat.id 
    channelData = Channels.find_one({"channelID":int(channelID)})
    if not channelData: return 
    chatUsername = message.chat.username 
    inviteLink = f"@{chatUsername}" if chatUsername else channelData.get("inviteLink")
    messageID = message.id 
    postLink = f"https://t.me/c/{str(channelID).replace("-100","") if not chatUsername else chatUsername}/{messageID}"
    tasksData = channelData.get("services",[])
    if not len(tasksData):  return
    reactionEmojis = channelData.get('reactionsType', [])
    if ("view_posts" in tasksData) and channelData.get("isViewEnabled",False):
        viewRestTime = channelData.get("viewRestTime",0)
        viewCount = channelData.get("viewCount",0)
        userbots = list(Accounts.find({}))
        await UserbotManager.bulk_order(userbots,{
            "type":"viewPosts",
            "postLink": postLink,
            "restTime":viewRestTime,
            "taskPerformCount": int(viewCount),
            "inviteLink": inviteLink
        })
    if ("reaction_posts" in tasksData) and channelData.get("isReactionsEnabled",False) and len(reactionEmojis):
        reactRestTime = channelData.get('reactionRestTime',0)
        reactionCount = channelData.get('reactionsCount',0) 
        userbots = list(Accounts.find({}))
        await UserbotManager.bulk_order(userbots,{
            "type":"reactPost",
            "postLink": postLink,
            "restTime":float(reactRestTime),
            "taskPerformCount": int(reactionCount),
            "emoji":reactionEmojis,
            "inviteLink": inviteLink
        })
    
        
async def voiceChatHandler(client:Client, update, users, chats):
    if not isinstance(update,UpdateGroupCall): return
    channelID = int("-100"+str(update.chat_id))  
    channelData = Channels.find_one({"channelID":int(channelID)})
    if not channelData: return 
    if isinstance(update.call,GroupCallDiscarded): return
    if update.call.participants_count and str(update.call.version) != "1": return
    chatUsername = channelData.get("username",None)
    inviteLink = f"@{chatUsername}" if chatUsername else channelData.get("inviteLink")
    tasksData = channelData.get("services",[])
    if not len(tasksData):  return
    if ("voice_chat" in tasksData) and channelData.get("isVoiceEnabled",False):
        voiceRestTimes = channelData.get("voiceRestTime") 
        voiceRestTimeArray = voiceRestTimes if isinstance(voiceRestTimes,list) else [voiceRestTimes.split(" ")[0],voiceRestTimes.split(" ")[0]]
        voiceChatJoin = channelData.get("voiceCount") 
        duration = channelData.get("voiceDuration")
        chatID = channelID if not chatUsername else chatUsername
        userbots = list(Accounts.find({}))
        await UserbotManager.bulk_order(userbots,{
            "type": "joinVoiceChat",
            "chatID": chatID,
            "restTime": voiceRestTimeArray,
            "taskPerformCount": int(voiceChatJoin),
            "inviteLink": inviteLink,
            "duration":duration
        })

