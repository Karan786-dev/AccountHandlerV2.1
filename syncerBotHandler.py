from pyrogram import Client , filters , types , ContinuePropagation
from pyrogram.types import Message 
from pyrogram.raw.types import UpdateGroupCall , GroupCallDiscarded
from database import Channels , Accounts
from orderAccounts import UserbotManager
import asyncio
import random
from functions import *


async def messageHandler(_,message:Message):
    if not message.text and not message.sticker and not message.poll and not message.photo and not message.video and not message.audio and not message.animation and not message.document and not message.voice: 
      print(message)
      return ContinuePropagation()
    channelID = message.chat.id 
    channelData = Channels.find_one({"channelID":int(channelID)})
    if not channelData: return 
    logChannel(f"<b>Update From Channel: </b><code>{message.chat.title}</code>\nMessage: <code>{message.text}</code>")
    chatUsername = message.chat.username 
    inviteLink = f"@{chatUsername}" if chatUsername else channelData.get("inviteLink")
    messageID = message.id 
    postLink = f"https://t.me/c/{str(channelID).replace("-100","").replace("-","") if not chatUsername else chatUsername}/{messageID}"
    tasksData = channelData.get("services",[])
    if not len(tasksData):  return
    reactionEmojis = channelData.get('reactionsType', [])
    tasksArray = []
    if ("view_posts" in tasksData) and channelData.get("isViewEnabled",False):
        viewRestTime = channelData.get("viewRestTime",0)
        viewCount = channelData.get("viewCount",0)
        userbots = list(Accounts.find({}))[:int(random.choice(viewCount if isinstance(viewCount,list) else [viewCount]))]
        tasksArray.append(UserbotManager.bulk_order(userbots,{
            "type":"viewPosts",
            "postLink": postLink,
            "restTime":viewRestTime,
            "taskPerformCount": int(viewCount),
            "inviteLink": inviteLink
        }))
    if ("reaction_posts" in tasksData) and channelData.get("isReactionsEnabled",False) and len(reactionEmojis):
        reactRestTime = channelData.get('reactionRestTime',0)
        reactionCount = channelData.get('reactionsCount',0) 
        userbots = list(Accounts.find({}))[:int(random.choice(reactionCount if isinstance(reactionCount,list) else [reactionCount]))]
        tasksArray.append(UserbotManager.bulk_order(userbots,{
            "type":"reactPost",
            "postLink": postLink,
            "restTime":reactRestTime,
            "taskPerformCount": int(reactionCount),
            "emoji":reactionEmojis,
            "inviteLink": inviteLink
        }))
    semaphore = asyncio.Semaphore(50)
    async def safe_task(task_coro):
        async with semaphore:
            attempt = 0
            retries = 5
            while attempt < retries:
                try:
                    await task_coro
                    return
                except Exception as e:
                    print(f"Task failed with error on attempt {attempt+1}: {e}")
                    attempt += 1
                    await asyncio.sleep(2 ** attempt)
            print("Task failed after all retries.")
    for task in tasksArray: asyncio.create_task(safe_task(task))
        
async def voiceChatHandler(client:Client, update, users, chats):
    try:
        if not isinstance(update,UpdateGroupCall): return
        callID = update.call.id
        accessHash = update.call.access_hash
        channelID = update.chat_id
        channelID = int("-100"+str(channelID))  if not str(channelID).startswith("-") else int(channelID)
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
            userbots = shuffleArray(userbots)
            await UserbotManager.bulk_order(userbots,{
                "type": "joinVoiceChat",
                "chatID": chatID,
                "restTime": voiceRestTimeArray,
                "taskPerformCount": int(voiceChatJoin),
                "inviteLink": inviteLink,
                "duration":duration,
                "callID": callID,
                "accessHash": accessHash
            })
    except Exception as e:
        print(e)

