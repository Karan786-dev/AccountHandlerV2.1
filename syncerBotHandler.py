from pyrogram import Client , filters , types
from pyrogram.types import Message 
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
            "restTime":float(viewRestTime),
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
    
        
async def voiceChatHandler(client:Client, message:Message):
    channelID = message.chat.id 
    channelData = Channels.find_one({"channelID":int(channelID)})
    if not channelData: return 
    chatUsername = message.chat.username 
    inviteLink = f"@{chatUsername}" if chatUsername else channelData.get("inviteLink")
    tasksData = channelData.get("services",[])
    if not len(tasksData):  return
    if ("voice_chat" in tasksData) and channelData.get("isVoiceEnabled",False):
        voiceRestTimes = channelData.get("voiceRestTime") 
        voiceRestTimeArray = voiceRestTimes if not isinstance(voiceRestTimes,list) else voiceRestTimes.split(" ")
        voiceChatJoin = channelData.get("voiceCount") 
        chatID = channelID if not chatUsername else chatUsername
        userbots = list(Accounts.find({}))
        await UserbotManager.bulk_order(userbots,{
            "type": "joinVoiceChat",
            "chatID": chatID,
            "restTime": float(random.choice(voiceRestTimeArray)),
            "taskPerformCount": int(voiceChatJoin),
            "inviteLink": inviteLink
        })
