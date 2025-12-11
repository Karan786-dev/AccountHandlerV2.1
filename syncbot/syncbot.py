import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
import monkeyPatches
from pyrogram import Client, filters, ContinuePropagation , idle
from pyrogram.types import Message
from database import Channels, Accounts
from config import *
from pathlib import Path
import time
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.types import UpdateGroupCall, GroupCallDiscarded
from telethon.tl.types import *
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.errors import *
from collections import deque
import json
from logger import logger
from functions import *
import asyncio

userbot_info = Accounts.find_one({"syncBot": True})
session_name = userbot_info.get("phone_number").replace("+", "")
pyrogram_session_string = userbot_info.get("session_string")
telethon_session_string = userbot_info.get("telethon_session_string",False)
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

if not telethon_session_string: 
    telethon_session_string = loop.run_until_complete(convert_pyrogram_to_telethon(f"../sessions/userbots/{session_name}", userbot_info.get("password", None)))
    # print(telethon_session_string)
    Accounts.update_one({"syncBot":True}, {"$set": {"telethon_session_string": telethon_session_string}})

sync_bot = TelegramClient(StringSession(telethon_session_string), API_ID, API_HASH)
pyro_bot = Client(name=USERBOT_SESSION +"/" + session_name,api_id=API_ID, api_hash=API_HASH, session_string=pyrogram_session_string, workdir=USERBOT_SESSION)

Path("syncbot/posts").mkdir(exist_ok=True)
message_ids_processed = {}
media_groups_processed = {}
post_activity = {} 
SPAM_LIMIT = 3
SPAM_INTERVAL = 2

@sync_bot.on(events.NewMessage(incoming=True))
async def handle_new_post(event):
    try:
        message = event.message
        if isinstance(message, MessageService):
            return
        if not message.peer_id or not isinstance(message.peer_id, PeerChannel):
            return
        channel_id = message.peer_id.channel_id
        channel_id = int("-100" + str(channel_id)) if not str(channel_id).startswith("-") else int(channel_id)
        message_id = message.id
        mediaGroupID = getattr(message.grouped_id, "to_int", lambda: None)()
        chat_entity = await event.get_chat()
        chat_title = chat_entity.title
        chat_username = chat_entity.username
        logger.debug(f"Post fetched from: {chat_title}")
        channel_data = Channels.find_one({"channelID": int(channel_id)})
        if not channel_data:
            return
        if str(channel_id) not in message_ids_processed:
            message_ids_processed[str(channel_id)] = []
        if str(channel_id) not in media_groups_processed:
            media_groups_processed[str(channel_id)] = []
        if message_id in message_ids_processed[str(channel_id)]:
            return
        else:
            message_ids_processed[str(channel_id)].append(message_id)

        if mediaGroupID:
            if mediaGroupID in media_groups_processed[str(channel_id)]:
                return
            else:
                media_groups_processed[str(channel_id)].append(mediaGroupID)
        if channel_data.get("spamProtection", False):
            if is_spam(message, {"spamLimit": SPAM_LIMIT, "spamInterval": SPAM_INTERVAL}):
                logger.warning(f"Spam detected in channel {chat_title}. Skipping post.")
                return
            else:
                post_activity.setdefault(str(channel_id), {'postsCount': 0})
                post_activity[str(channel_id)]['postsCount'] += 1
                if post_activity[str(channel_id)]['postsCount'] >= SPAM_LIMIT:
                    logger.info(f"Resetting posts count for channel {channel_id} after reaching limit.")
                    await resetPosts(channel_id)
        if channel_data.get("title") != chat_title:
            Channels.update_one({"channelID": int(channel_id)}, {"$set": {"title": chat_title}})

        if channel_data.get("username") != chat_username:
            Channels.update_one({"channelID": int(channel_id)}, {"$set": {"username": chat_username}})
        invite_link = f"@{chat_username}" if chat_username else channel_data.get("inviteLink")
        post_link = f"https://t.me/c/{str(channel_id).replace('-100', '')}/{message_id}" if not chat_username else f"https://t.me/{chat_username}/{message_id}"
        validity = channel_data.get("validity")
        daysLeft = int(channel_data.get("daysLeft", 0))
        if validity and (not daysLeft):
            return
        tasks_data = channel_data.get("services", [])
        if not tasks_data:
            return
        reaction_emojis = channel_data.get('reactionsType', [])
        tasks_array = []
        text = (
            "<b>Alert: New Post Detected</b>\n\n"
            f"<b>Channel: <a href='{invite_link.replace('@', 'https://t.me/')}'>{chat_title}</a></b>\n"
            f"<b>Post Link: </b><a href='{post_link}'>{post_link}</a>\n"
            f"<b>Tasks: </b><code>{', '.join(tasks_data)}</code>\n\n"
        )
        if "view_posts" in tasks_data and channel_data.get("isViewEnabled", False):
            view_rest_time = channel_data.get("viewRestTime", 0)
            view_count = channel_data.get("viewCount", 0)
            view_count = random.randint(view_count[0], view_count[1] if len(view_count) > 1 else view_count[0]) if isinstance(view_count, list) else view_count
            userbots = list(Accounts.find({},{"_id":0,"added_at":0}))[:int(view_count)]
            tasks_array.append({
                "type": "viewPosts",
                "chatID": channel_id,
                "postLink": post_link,
                "restTime": view_rest_time,
                "taskPerformCount": int(view_count),
                "inviteLink": invite_link,
                "userbots":userbots
            })
            text += (
                f"<b>📊 Views:</b>\n"
                f"<b>├─ Views Count</b>: <code>{view_count}</code>\n"
                f"<b>├─ Delay: </b><code>{view_rest_time}</code>\n\n"
            )
        if ("reaction_posts" in tasks_data and channel_data.get("isReactionsEnabled", False) and reaction_emojis) and not filterAd(message.message):
            react_rest_time = channel_data.get('reactionRestTime', 0)
            reaction_count = channel_data.get('reactionsCount', 0)
            reaction_count = random.choice(reaction_count) if isinstance(reaction_count, list) else reaction_count
            userbots = list(Accounts.find({},{"_id":0,"added_at":0}))[:int(reaction_count)]
            tasks_array.append({
                "type": "reactPost",
                "postLink": post_link,
                "chatID": channel_id,
                "restTime": react_rest_time,
                "taskPerformCount": int(reaction_count),
                "emoji": reaction_emojis,
                "inviteLink": invite_link,
                "userbots":userbots
            })
            text += (
                f"<b>🎭 Auto Reactions:</b>\n"
                f"<b>├─ Reactions Count</b>: <code>{reaction_count}</code>\n"
                f"<b>├─ Delay: </b><code>{react_rest_time}</code>\n"
                f"<b>├─ Emoji's: </b><code>{' '.join(reaction_emojis) or 'None'}</code>"
            )
        if "auto_votes" in tasks_data and channel_data.get("isVoteEnabled", False) and message.poll:
            message: MessageMediaPoll = message
            voteDelay = channel_data.get("voteRestTime", 0)
            votesCount = channel_data.get("votesCount", 0)
            votesCount = [votesCount,votesCount] if isinstance(votesCount, (int,str)) else votesCount 
            # print(votesCount)
            votesCount = random.randint(int(votesCount[0]), int(votesCount[1]))
            userbots = list(Accounts.find({"$or": [{"syncBot": {"$exists": False}}, {"syncBot": False}, {"helperBot": {"$exists": False}}, {"helperBot": False}]}, {"_id": 0, "added_at": 0}))
            optionsPerc = channel_data.get("optionsPercentage", {})
            for i in userbots:
                if not i.get("syncBot", False) and not i.get("helperBot", False):
                    continue
                userbots.remove(i)
                logger.warning(f"Userbot {i.get('phone_number')} is a sync or helper bot, removing from userbots list.")
            text += (
                f"\n\n<b>🗳️ Auto Votes:</b>\n"
                "<b>├─ Votes Count</b>: <code>{totalVotes}</code>\n"
                f"<b>├─ Delay: </b><code>{voteDelay}</code>\n"
            )
            totalOptionsDone = 0
            realTotalVotesOnOptions = 0
            optionsPerc = dict(sorted((json.loads(optionsPerc) if isinstance(optionsPerc,str) else optionsPerc).items(), key=lambda item: item[1], reverse=True))
            for i in optionsPerc:
                
                if totalOptionsDone == len(message.poll.poll.answers):
                    
                    break
                totalOptionsDone += 1
                percentage = optionsPerc[i]
                if not percentage:
                    continue
                optionVoteCount = (float(percentage) / 100) * int(votesCount)
                selectedBots = userbots[:int(optionVoteCount)]
                logger.debug(f"Option {i} Vote Count: {optionVoteCount}, Selected Bots: {len(selectedBots)}")
                taskData = {
                    "type": "votePoll",
                    "chatID": channel_id,
                    "messageID": message_id,
                    "optionIndex": i,
                    "restTime": voteDelay,
                    "taskPerformCount": len(selectedBots),
                    "inviteLink": invite_link,
                    "userbots": selectedBots
                }
                text += f"<b>├─ Option {int(i)+1}:</b> <code>{percentage}% ({len(selectedBots)})</code>\n"
                realTotalVotesOnOptions += len(selectedBots)
                tasks_array.append(taskData)
                userbots = [account for account in userbots if account not in selectedBots]
                
            text = text.replace("{totalVotes}", str(realTotalVotesOnOptions))
        await logChannel(text,printLog=False)
        for task in tasks_array:
            task_file = Path(f"syncbot/posts/{task.get('type')}_{str(channel_id).replace('-','')}-{message.id}-{generateRandomString()}.json")
            with open(task_file, "w", encoding="utf-8") as f:
                json.dump(task, f, indent=4, ensure_ascii=False)
        return
    except Exception as error:
        raise error


@sync_bot.on(events.Raw())
async def handle_voice_chats(event):
    update = event
    if not isinstance(update, UpdateGroupCall):
        return
    if isinstance(update.call, GroupCallDiscarded):
        return
    channel_id = update.chat_id
    channel_id = int("-100" + str(channel_id)) if not str(channel_id).startswith("-") else int(channel_id)
    call_id = update.call.id
    access_hash = update.call.access_hash
    channel = Channels.find_one({"channelID": channel_id})
    if not channel:
        return
    logger.debug(f"Voice chat detected in channel: {channel.get('title', 'Unknown')} (ID: {channel_id})")

    if update.call.participants_count and str(update.call.version) != "1":
        return
    services = channel.get("services", [])
    if (not services) or ("voice_chat" not in services) or (not channel.get("isVoiceEnabled", False)):
        return

    chat_username = channel.get("username", None)
    invite = f"@{chat_username}" if chat_username else channel.get("inviteLink")
    rest_time = channel.get("voiceRestTime")
    duration = channel.get("voiceDuration")
    voice_count = channel.get("voiceCount")
    delay = rest_time if isinstance(rest_time, list) else [rest_time, rest_time]
    voice_data = {
        "type": "joinVoiceChat",
        "chatID": chat_username or channel_id,
        "inviteLink": invite,
        "duration": duration,
        "restTime": delay,
        "taskPerformCount": voice_count,
        "callID": call_id,
        "accessHash": access_hash
    }
    text = (
        "<b>Voice Chat Detected</b>\n\n"
        f"<b>Channel: <a href='{invite.replace('@', 'https://t.me/')}'>{channel.get('title')}</a></b>\n"
        f"<b>Invite Link: </b><code>{invite}</code>\n"
        f"<b>Call ID: </b><code>{call_id}</code>\n"
        f"<b>Access Hash: </b><code>{access_hash}</code>\n"
        f"<b>Rest Time: </b><code>{delay}</code>\n"
        f"<b>Duration: </b><code>{duration}</code>\n"
        f"<b>Count: </b><code>{voice_count}</code>"
    )
    await logChannel(text, printLog=False)
    voice_file = Path(f"syncbot/posts/voice_{channel_id}_{call_id}.json")
    with open(voice_file, "w", encoding="utf-8") as f:
        json.dump(voice_data, f, indent=4, ensure_ascii=False)
    return ContinuePropagation()

async def join_missing_channels():
    me = await sync_bot.get_me()
    logger.debug(f"{me.username or me.first_name} joining channels...")
    while True:
        # await sync_bot.send_message("@xr_karan","Hello World")
        try:
            channels = Channels.find({"joinedBySyncBot": {"$ne": True}})
            for ch in channels:
                chat_id = ch.get("channelID")
                invite_link = ch.get("inviteLink")
                if not invite_link:
                    continue
                try:
                    await pyro_bot.join_chat(invite_link)
                    Channels.update_one({"_id": ch["_id"]}, {"$set": {"joinedBySyncBot": True}})
                    await logChannel(
                        f"<b>Syncbot joined: </b><code>{ch.get('title', 'Unknown')} </code>(<b>ID: </b><code>{chat_id}</code>)\n"
                        f"<b>Invite Link:</b><code> {invite_link}</code>\n\n"
                        f"<b>Services will be continue for this channel.</b>"
                        , printLog=False
                    )
                except UserAlreadyParticipant:
                    Channels.update_one({"_id": ch["_id"]}, {"$set": {"joinedBySyncBot": True}})
                    await logChannel(
                        f"<b>Syncbot joined: </b><code>{ch.get('title', 'Unknown')} </code>(<b>ID: </b><code>{chat_id}</code>)\n"
                        f"<b>Invite Link:</b><code> {invite_link}</code>\n\n"
                        f"<b>Services will be continue for this channel.</b>"
                        , printLog=False
                    )
                except InviteHashExpired:
                    logger.critical(f"[{ch.get("title",None)}: {invite_link}] Removed: Invite link expired or invalid")
                    Channels.delete_one({"_id": ch["_id"]})
                    continue
                except FloodWait as e:
                    logger.warning(f"FloodWait for {e.value} seconds while joining {invite_link}")
                    await asyncio.sleep(e.value)
                except Exception as ex:
                    logger.error(f"Unexpected error joining {invite_link}: {ex}")
                await asyncio.sleep(2)
        except Exception as e:
            logger.exception(f"Error in join_missing_channels loop: {e}")
        await asyncio.sleep(60)
        
def is_spam(message, cfg):
    now = message.date.timestamp()
    chan = message.peer_id.channel_id
    dq = post_activity.setdefault(chan, deque())
    while dq and now - dq[0] > cfg["spamInterval"]: dq.popleft() 

    if len(dq) >= cfg["spamLimit"]: return True

    dq.append(now)
    return False

async def resetPosts(channelID):
    await asyncio.sleep(SPAM_INTERVAL)
    post_activity[str(channelID)]['postsCount'] = 0
    
import datetime, gc

async def heartbeat():
    while True:
        logger.info(f"✅ Heartbeat: Bot alive at {datetime.datetime.now()}")
        gc.collect()  # Help free up memory
        await asyncio.sleep(60)  # Every 5 minutes

sync_bot.start()
pyro_bot.start()
print("✅ SyncBot started.")

loop.create_task(join_missing_channels())
loop.create_task(heartbeat())

try:
    loop.run_until_complete(sync_bot.run_until_disconnected())
except KeyboardInterrupt:
    pyro_bot.stop()
    print("🛑 SyncBot stopped.")
finally:
    loop.close()