import monkeyPatches
from pyrogram import Client 
import asyncio 
from pytgcalls import PyTgCalls 
from pytgcalls.exceptions import *
import ntgcalls
# removed threading.Timer use because we schedule delayed leaves with asyncio
from urllib.parse import urlparse
import random
from pyrogram.errors import *
from pyrogram.raw.functions.messages import GetMessagesViews
from pyrogram.raw.types import InputPeerNotifySettings , InputReportReasonSpam  , InputNotifyPeer
from pyrogram.raw.functions.account import ReportPeer , UpdateNotifySettings 
from functions import *
import time
import unicodedata
from logger import logger
from database import *

async def viewPost(task,client: Client,phone_number,self,taskID):
    postLink = task["postLink"].replace("/c/","/")
    parsed_url = urlparse(postLink)
    path_segments = parsed_url.path.strip("/").split("/")
    chatID = str(path_segments[0])
    messageID = int(path_segments[1])
    if is_number(chatID):
        chatID = int("-100"+chatID)  if  not chatID.startswith("-") else int(chatID)
        messageID = int(path_segments[1])
    if not is_number(chatID):
        channelData = await client.get_chat(chatID)
        chatID = channelData.id
    task['chatID'] = chatID
    try:
        channelPeer = await client.resolve_peer(chatID)
        res = await client.invoke(GetMessagesViews(
            peer=channelPeer,
            id=[messageID],
            increment=True
            )
        )
    except Exception as e: raise e

async def sendPhoto(task,client: Client,phone_number,self,taskID):
    photoLink = task['photoLink']
    chatIDToDeliver = task['chatID']
    chat_username, message_id = photoLink.split('/')[-2:]
    message_id = int(message_id)
    try:
        fileChat = await client.get_chat(chat_username)
        message = await client.get_messages(fileChat.id, message_id)
        fileID = message.photo.file_id
        await client.send_photo(chat_id=chatIDToDeliver, photo=fileID)
        logger.debug(f"Photo Delivered To {chatIDToDeliver} By: {phone_number}")
    except Exception as e:
        logger.error(f"{phone_number}: Failed To Send Photo: {str(e)}")
        raise e

async def votePoll(task,client: Client,phone_number,self,taskID):
    chatID = "@"+task["chatID"] if not is_number(task["chatID"]) else int(task["chatID"])
    messageID = int(task["messageID"])
    try: 
        if not await joinIfNot(client,chatID,task.get("inviteLink",None)): return
        voteResult = await client.vote_poll(chatID,messageID,int(task["optionIndex"]))
        if voteResult: logger.debug(f"Userbot {phone_number} voted on {chatID} with {task['optionIndex']}")
        else: logger.warning(f"{phone_number} Failed To Vote: {chatID} with {task['optionIndex']}")
    except Exception as e: 
        logger.error(f"{phone_number} Failed To Vote: {str(e)}")
        raise e

async def sendMessage(task,client: Client,phone_number,self,taskID):
    textToDeliver = task['text']
    chatIDToDeliver = task['chatID']
    await client.send_message(chatIDToDeliver,textToDeliver)
    logger.debug(f"Message Delivered By: {phone_number}")

async def reactPost(task,client: Client,phone_number,self,taskID):
    postLink = task["postLink"].replace("/c/","/")
    parsed_url = urlparse(postLink)
    path_segments = parsed_url.path.strip("/").split("/")
    chatID = str(path_segments[0])
    messageID = int(path_segments[1])
    if is_number(chatID): chatID = int("-100"+chatID)  if  not chatID.startswith("-") else int(chatID)
    emojis = task['emoji']
    emojiString = random.choice(emojis)
    emoji = unicodedata.normalize("NFKC", emojiString)
    try: await client.send_reaction(chatID,messageID,emoji=emoji)
    except ReactionInvalid: pass
        # logger.warning(f"{phone_number}: <b>[{emojiString}] Not Allowed</b> In <code>{chatID}</code>")
    except ReactionsTooMany: pass
    except MessageIdInvalid: pass
    except ChatWriteForbidden: pass
    except Exception as e: raise e

async def leaveVc(task,client: Client,phone_number,self,taskID):
    chatID = task["chatID"]
    try:
        app = PyTgCalls(client)
        await app.leave_call(chatID)
        logger.debug(f"{phone_number} had leaved the call.")
    except GroupcallForbidden: self.stopTask(taskID)
    except Exception as e: 
        logger.error("Error While Leaving Call: "+str(e))
        raise e


async def joinVc(task,client: Client,phone_number,self,taskID):
    chatID = task["chatID"]
    inviteLink = task.get("inviteLink",None)
    duration = task.get("duration",0) 
    finalDuration =  0
    if not isinstance(duration,list): finalDuration = duration
    elif isinstance(duration,list) and len(duration) == 2: finalDuration = random.randint(int(duration[0]),int(duration[1]))
    elif isinstance(duration,list) and len(duration) == 1: finalDuration = duration[0]
    else: finalDuration = duration
    try:
        app = PyTgCalls(client)
        try:
            await app.start()
            await app.play(
                chat_id=chatID,
            )
        except (ntgcalls.ConnectionError, ntgcalls.ConnectionNotFound, ntgcalls.TelegramServerError) as e:
            logger.warning(f"{phone_number}: PyTgCalls start/play failed: {e}")
            try:
                await app.stop()
            except Exception:
                pass
            return
        if finalDuration:
            async def _delayed_leave():
                try:
                    await asyncio.sleep(float(finalDuration))
                    await app.leave_call(chatID)
                except Exception:pass

            delayed_task = asyncio.create_task(_delayed_leave())
            def _delayed_done(t):
                try:
                    if t.cancelled():
                        return
                    exc = t.exception()
                    if exc:
                        logger.warning(f"Delayed leave task for {phone_number} raised: {exc}")
                except Exception: pass

            delayed_task.add_done_callback(_delayed_done)
    except ChannelInvalid:
        await client.join_chat(inviteLink)
        await self.add_task(task, None)
    except (ChatAdminRequired, GroupcallForbidden):
        pass
    except (ntgcalls.ConnectionError, ntgcalls.ConnectionNotFound, ntgcalls.TelegramServerError):
        pass
    except Exception as e:
        logger.error(f"Error While Joining Call: {str(e)}")
        raise e

async def reportChat(task,client: Client,phone_number,self,taskID):
    try:
        chatID = task["chatID"]
        if str(chatID).startswith("-"): await joinIfNot(client,chatID,task.get("inviteLink",None))
        input_channel = await client.resolve_peer(str(chatID))
        res = await client.invoke(
            ReportPeer(
                peer=input_channel,
                message="Spam",
                reason=InputReportReasonSpam()
            )
        )
        logger.debug(f"Userbot {phone_number} reported {chatID}: {res}")
    except FloodWait as e:
        logger.warning(f"{phone_number}: Flood Wait: {e.value} seconds")
        await asyncio.sleep(e.value)
        await self.add_task(task, None)
    except (PeerIdInvalid, ChannelPrivate, ChannelInvalid):
        logger.warning(f"{phone_number}: Invalid Peer ID for {chatID}. Retrying...")
        await joinIfNot(client,chatID,task.get("inviteLink",None))
        await self.add_task(task, None)
    except Exception as e:
        logger.error(f"{phone_number}: Failed To Report: {str(e)}", True)
        raise e

async def leaveChannel(task,client: Client,phone_number,self,taskID):
    for channel in task["channels"]:
        try:
            chatData = await client.get_chat(str(channel))
            channel = chatData.id
            Chats.update_one({"phone_number": str(channel)},{"$pull": {"joined": channel}},upsert=True)
            await client.leave_chat(channel,delete=True)
            # logger.debug(f"Userbot {phone_number} leaved {channel}")
        except UserNotParticipant: pass
        except Exception as e:
            if str(e) == "'ChatPreview' object has no attribute 'id'": return
            raise e

async def joinChannel(task,client: Client,phone_number,self,taskID):
    for channel in task["channels"]:
        try:
            if not is_number(channel):
                channelData = await client.get_chat(channel)
                channel = getattr(channelData,"id",channel)
            chatData = await client.join_chat(channel)
            channel = chatData.id
            Chats.update_one({"phone_number": str(phone_number)},{"$addToSet": {"joined": channel}},upsert=True)
            # logger.debug(f"Userbot {phone_number} joined {channel}")
        except UserAlreadyParticipant: pass
        except Exception as err: raise err
        rest_time = task.get("restTime", 0)
        if isinstance(rest_time,list) and len(rest_time) > 1:
            rest_time = random.randint(int(rest_time[0]),int(rest_time[1]))
        elif isinstance(rest_time,list) and len(rest_time) == 1: rest_time = rest_time[0]
        # logger.critical(f"Random Rest time: {rest_time}")
        await asyncio.sleep(float(rest_time))

async def mute_unmute(task,client: Client,phone_number,self,taskID):
    try:
        chatID: str = task["chatID"]
        # If Duration is 0 then channel will be unmuted
        foreverTime = 2147483647
        duration:int = task.get("duration",foreverTime) #Default number 2147483647 is for forever mute 
        finalDuration = duration if not isinstance(duration,list) else random.randint(int(duration[0]),int(duration[1]))
        channelInfo = await joinIfNot(client,chatID,task.get("inviteLink",None))
        chatID = channelInfo.id if (channelInfo or str(chatID).isdigit()) else int(chatID)
        async for dialog in client.get_dialogs():
            if dialog.chat.id == chatID: break

        channelPeer = await client.resolve_peer(chatID)
        mute_untill = (int(time.time()) + finalDuration) if not finalDuration == foreverTime else foreverTime
        if not int(finalDuration): mute_untill = 0
        res = await client.invoke(
                UpdateNotifySettings(
                    peer=InputNotifyPeer(peer=channelPeer),
                    settings=InputPeerNotifySettings(
                        show_previews=False,
                        silent=False,
                        mute_until=mute_untill
                    )
                )
            )
        
        if mute_untill:
            logger.info(f"[{phone_number}]: Muted {chatID} untill {mute_untill}")
            if int(chatID) == -1003060090488: await logChannel(f"[{phone_number}]: Unmuted {chatID}: {res}")
        else: 
            if int(chatID) == -1003060090488: await logChannel(f"[{phone_number}]: Unmuted {chatID}: {res}")
            logger.info(f"[{phone_number}]: Unmuted {chatID}")
        updateQuery = {"$addToSet": {"muted": chatID}} if mute_untill else {"$pull": {"muted": chatID}}
        Chats.update_one({"phone_number": phone_number.replace("+","")},updateQuery,upsert=True)
    except Exception as err:  raise err


async def changeProfileName(task,client: Client,phone_number,self=None,taskID=None):
    try:
        firstName = task["firstName"]
        lastName = task.get("lastName","")
        fullName = firstName + " " + lastName
        await client.update_profile(first_name=firstName,last_name=lastName)
        # logger.debug(f"Userbot {phone_number} changed name to `{fullName}`")
    except Exception as e: 
        logger.critical(f"[{phone_number}]: Error while changing name {e}")
        raise e
    
async def changeProfilePicture(task,client: Client,phone_number: str,self=None,taskID=None):
    try: 
        photoPath = task["photo"]
        await client.set_profile_photo(photo=photoPath)
    except Exception as e: raise e