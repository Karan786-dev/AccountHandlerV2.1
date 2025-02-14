from pyrogram import Client , filters , types , ContinuePropagation
from pyrogram.types import Message 
from database import Channels , Accounts
from orderAccounts import UserbotManager
import asyncio
from urllib.parse import urlparse
from functions import *
from ..responses.responseFunctions import getResponse


@Client.on_message(filters.text)
async def onBoosterLink(_:Client,message:Message):
    if not message.text.startswith("https://t.me/c") and not message.text.startswith("https://t.me/"): raise ContinuePropagation()
    if getResponse(message.from_user.id): raise ContinuePropagation()
    postLink = message.text.replace('/c',"")
    parsed_url = urlparse(postLink)
    path_segments = parsed_url.path.strip("/").split("/")
    channelID = str(path_segments[0])
    if not is_number(channelID):
        chatInfo = await _.get_chat(channelID)
        channelID = str(chatInfo.id)
    if is_number(channelID) and not channelID.startswith("-100"): channelID = int(("-100"+path_segments[0]))
    channelData = Channels.find_one({"channelID":int(channelID)})
    if not channelData or not channelData.get("isBoosterEnabled",False): raise ContinuePropagation()
    messageID = int(path_segments[1])
    inviteLink = channelData.get("inviteLink")
    postLink = f"https://t.me/c/{str(channelID).replace("-100","")}/{messageID}"
    tasksData = channelData.get("services",[])
    if not len(tasksData):  return
    reactionEmojis = channelData.get('reactionsType', [])
    tasksArray = []
    if ("view_posts" in tasksData) and channelData.get("isViewEnabled",False):
        viewCount = channelData.get("viewCount",0)
        userbots = list(Accounts.find({}))
        tasksArray.append(UserbotManager.bulk_order(userbots,{
            "type":"viewPosts",
            "postLink": postLink,
            "restTime":0,
            "taskPerformCount": int(viewCount),
            "inviteLink": inviteLink
        }))
    if ("reaction_posts" in tasksData) and channelData.get("isReactionsEnabled",False) and len(reactionEmojis):
        reactionCount = channelData.get('reactionsCount',0) 
        userbots = list(Accounts.find({}))
        tasksArray.append(UserbotManager.bulk_order(userbots,{
            "type":"reactPost",
            "postLink": postLink,
            "restTime":0,
            "taskPerformCount": int(reactionCount),
            "emoji":reactionEmojis,
            "inviteLink": inviteLink
        }))
    if not len(tasksArray): return 
    waitingMsg = await message.reply("<b>Starting</b> Tasks...")
    await asyncio.gather(*tasksArray)
    await _.edit_message_text(message.from_user.id,waitingMsg.id,"✅ All Services is <b>completed</b> on this post")

@Client.on_message(filters.forwarded)
async def onBoosterForward(_:Client,message:Message):
    if not message.forward: raise ContinuePropagation()
    channelID = message.forward_from_chat.id
    channelData = Channels.find_one({"channelID":channelID})
    if not channelData or not channelData.get("isBoosterEnabled",False): raise ContinuePropagation()
    chatUsername = message.forward_from_chat.username 
    inviteLink = f"@{chatUsername}" if chatUsername else channelData.get("inviteLink")
    messageID = message.forward_from_message_id 
    postLink = f"https://t.me/c/{str(channelID).replace("-100","").replace("-","") if not chatUsername else chatUsername}/{messageID}"
    tasksData = channelData.get("services",[])
    if not len(tasksData):  return
    reactionEmojis = channelData.get('reactionsType', [])
    tasksArray = []
    if ("view_posts" in tasksData) and channelData.get("isViewEnabled",False):
        viewCount = channelData.get("viewCount",0)
        userbots = list(Accounts.find({}))
        tasksArray.append(UserbotManager.bulk_order(userbots,{
            "type":"viewPosts",
            "postLink": postLink,
            "restTime":0,
            "taskPerformCount": int(viewCount),
            "inviteLink": inviteLink
        }))
    if ("reaction_posts" in tasksData) and channelData.get("isReactionsEnabled",False) and len(reactionEmojis):
        reactionCount = channelData.get('reactionsCount',0) 
        userbots = list(Accounts.find({}))
        tasksArray.append(UserbotManager.bulk_order(userbots,{
            "type":"reactPost",
            "postLink": postLink,
            "restTime":0,
            "taskPerformCount": int(reactionCount),
            "emoji":reactionEmojis,
            "inviteLink": inviteLink
        }))
    if not len(tasksArray): return 
    waitingMsg = await message.reply("<b>Starting</b> Tasks...")
    await asyncio.gather(*tasksArray)
    await _.edit_message_text(message.from_user.id,waitingMsg.id,"✅ All Services is <b>completed</b> on this post")