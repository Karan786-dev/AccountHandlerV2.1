from pyrogram import Client , filters , types , ContinuePropagation
from pyrogram.types import Message 
from database import Channels , Accounts
from orderAccounts import UserbotManager
import asyncio
from urllib.parse import urlparse
from functions import *
from config import *
from collections import deque


boosterBot = Client(SESSION+"/booster",api_id=API_ID,api_hash=API_HASH,bot_token=BOT_TOKEN_BOOSTER)
post_activity = {} 
SPAM_LIMIT = 5
SPAM_INTERVAL = 2



@boosterBot.on_message(filters.text & filters.private)
async def onBoosterLink(_:Client,message:Message):
    if not message.text.startswith("https://t.me/c/") and not message.text.startswith("https://t.me/"): raise ContinuePropagation()
    postLink = message.text.replace('/c/',"/")
    parsed_url = urlparse(postLink)
    path_segments = parsed_url.path.strip("/").split("/")
    channelID = str(path_segments[0])
    if not is_number(channelID):
        try:chatInfo = await _.get_chat(channelID)
        except Exception as e: return await message.reply(f"Error: {str(e)}")
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

message_ids_processed = {}
media_groups_processed = {}


@boosterBot.on_message(filters.forwarded)
async def onBoosterForward(_:Client,message:Message):
    if not message.forward or not message.forward_from_chat: raise ContinuePropagation()
    channelID = message.forward_from_chat.id
    channelData = Channels.find_one({"channelID":channelID})
    if not channelData or not channelData.get("isBoosterEnabled",False): raise ContinuePropagation()
    validity = channelData.get("validity")
    daysLeft = int(channelData.get("daysLeft",0))
    if validity and (not daysLeft): return await message.reply_text(f"<b>[{channelData.get("title")}]: Validity Expired Bruh!!</b>")
    if channelData.get("spamProtection", False):
        if is_spam(message, {"spamLimit": SPAM_LIMIT, "spamInterval": SPAM_INTERVAL}):
            await message.reply_text(f"<b>Spam Detected! Please wait {SPAM_INTERVAL} seconds before sending more posts.</b>",reply_to_message_id=message.id)
            raise ContinuePropagation()
        else:
            post_activity.setdefault(str(channelID), {'postsCount': 0})
            post_activity[str(channelID)]['postsCount'] += 1
            if post_activity[str(channelID)]['postsCount'] >= SPAM_LIMIT:
                await resetPosts(channelID)
    
    
    chatUsername = message.forward_from_chat.username 
    inviteLink = f"@{chatUsername}" if chatUsername else channelData.get("inviteLink")
    messageID = message.forward_from_message_id 
    postLink = f"https://t.me/c/{str(channelID).replace("-100","").replace("-","") if not chatUsername else chatUsername}/{messageID}"
    # print(postLink)
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
    mediaGroupID = message.media_group_id
    if str(channelID) not in message_ids_processed:
        message_ids_processed[str(channelID)] = []
    if str(channelID) not in media_groups_processed:
        media_groups_processed[str(channelID)] = []

    if mediaGroupID:
        if mediaGroupID in media_groups_processed[str(channelID)]:
            raise ContinuePropagation()
        else:
            media_groups_processed[str(channelID)].append(mediaGroupID)
    else:
        if message.forward_from_message_id in message_ids_processed[str(channelID)]:
            await message.reply_text("This post has already been processed.", reply_to_message_id=message.id)
            raise ContinuePropagation()
    waitingMsg = await message.reply_text("<b>Starting</b> Tasks...",reply_to_message_id=message.id)
    await asyncio.gather(*tasksArray)
    message_ids_processed[str(channelID)].append(message.forward_from_message_id)
    await _.edit_message_text(message.from_user.id,waitingMsg.id,"✅ All Services is <b>completed</b> on this post")


def is_spam(message, cfg):
    now = message.date.timestamp()
    chan = message.chat.id
    dq = post_activity.setdefault(chan, deque())
    while dq and now - dq[0] > cfg["spamInterval"]: dq.popleft() 

    if len(dq) >= cfg["spamLimit"]: return True

    dq.append(now)
    return False

async def resetPosts(channelID):
    await asyncio.sleep(SPAM_INTERVAL)
    post_activity[str(channelID)]['postsCount'] = 0