from pyrogram import Client , filters , types , ContinuePropagation
from pyrogram.types import Message 
from pyrogram.raw.types import UpdateGroupCall , GroupCallDiscarded
from database import Channels , Accounts
from orderAccounts import UserbotManager
import asyncio
import random
from functions import *


async def messageHandler(_: Client,message:Message):
    if message.service: return ContinuePropagation()
    channelID = message.chat.id 
    channelData = Channels.find_one({"channelID":int(channelID)})
    if not channelData: return 
    chatUsername = message.chat.username 
    inviteLink = f"@{chatUsername}" if chatUsername else channelData.get("inviteLink")
    messageID = message.id 
    postLink = f"https://t.me/{str(channelID).replace("-100","").replace("-","") if not chatUsername else chatUsername}/{messageID}"
    tasksData = channelData.get("services",[])
    if not len(tasksData):  return
    reactionEmojis = channelData.get('reactionsType', [])
    tasksArray = []
    text = (
            "<b>Alert: New Post Detected</b>\n\n"
            f"<b>Channel: <a href='{inviteLink.replace('@','https://t.me/')}'>{channelData.get('title')}</a></b>\n"
            f"<b>Post Link: </b><a href='{postLink}'>{postLink}</a>\n"
            f"<b>Tasks: </b><code>{', '.join(tasksData)}</code>\n\n"
    )
    if ("view_posts" in tasksData) and channelData.get("isViewEnabled",False):
        viewRestTime = channelData.get("viewRestTime",0)
        viewCount = channelData.get("viewCount",0)
        userbots = list(Accounts.find({}))[:int(random.choice(viewCount if isinstance(viewCount,list) else [viewCount]))]
        tasksArray.append(asyncio.create_task(UserbotManager.bulk_order(userbots,{
            "type":"viewPosts",
            "postLink": postLink,
            "restTime":viewRestTime,
            "taskPerformCount": int(viewCount),
            "inviteLink": inviteLink
        })))
        text += (
            f"<b>📊 Views:</b>\n"
            f"<b>├─ Views Count</b>: <code>{viewCount}</code>\n"
            f"<b>├─ Delay: </b><code>{viewRestTime}</code>\n\n"
        )
    if ("reaction_posts" in tasksData) and channelData.get("isReactionsEnabled",False) and len(reactionEmojis):
        reactRestTime = channelData.get('reactionRestTime',0)
        reactionCount = channelData.get('reactionsCount',0) 
        userbots = list(Accounts.find({}))[:int(random.choice(reactionCount if isinstance(reactionCount,list) else [reactionCount]))]
        tasksArray.append(asyncio.create_task(UserbotManager.bulk_order(userbots,{
            "type":"reactPost",
            "postLink": postLink,
            "restTime":reactRestTime,
            "taskPerformCount": int(reactionCount),
            "emoji":reactionEmojis,
            "inviteLink": inviteLink
        })))
        text += (
            f"<b>🎭 Auto Reactions:</b>\n"
            f"<b>├─ Reactions Count</b>: <code>{reactionCount}</code>\n"
            f"<b>├─ Delay: </b><code>{reactRestTime}</code>\n"
            f"<b>├─ Emoji's: </b><code>{' '.join(reactionEmojis) or 'None'}</code>"
        )
    if len(tasksArray): 
        logChannel(text,printLog=False)
        asyncio.gather(*tasksArray)
        
async def voiceChatHandler(client:Client, update, users, chats):
    try:
        if not isinstance(update,UpdateGroupCall): return ContinuePropagation()
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
            logChannel(
                (
                    "<b>🎙 Alert: Live Stream Started</b>\n\n"
                    f"<b>├─ Channel: <a href='{inviteLink.replace("@","https://t.me/")}'>{channelData.get("title")}</a>\n</b>"
                    f"<b>├─ Delay: </b><code>{voiceRestTimeArray}</code>\n"
                    f"<b>├─ Count: </b><code>{voiceChatJoin}</code>\n"
                    f"<b>├─ Duration: </b><code>{duration}</code>"
                ),
                printLog=False
            )
            asyncio.create_task(UserbotManager.bulk_order(userbots,{
                "type": "joinVoiceChat",
                "chatID": chatID,
                "restTime": voiceRestTimeArray,
                "taskPerformCount": int(voiceChatJoin),
                "inviteLink": inviteLink,
                "duration":duration,
                "callID": callID,
                "accessHash": accessHash
            }))
    except Exception as e:
        raise e

