from pyrogram import Client , filters
from pytgcalls import filters as callFilters
from config import USERBOT_SESSION
import asyncio 
from pytgcalls import PyTgCalls 
from pytgcalls.exceptions import *
from threading import Timer
from urllib.parse import urlparse
import random
from pyrogram.errors import *
from pyrogram.raw.functions.messages import GetMessagesViews
from database import Accounts , Channels
from pyrogram.handlers import MessageHandler , RawUpdateHandler
from pyrogram.raw.types import InputPeerNotifySettings , InputReportReasonSpam  , InputNotifyPeer
from pyrogram.raw.functions.account import ReportPeer , UpdateNotifySettings 
from pyrogram.enums import ChatMemberStatus
from functions import *
import os
import time
import unicodedata
from logger import logger

async def viewPost(task,client: Client,phone_number,self,taskID):
    postLink = task["postLink"].replace("/c","")
    parsed_url = urlparse(postLink)
    path_segments = parsed_url.path.strip("/").split("/")
    chatID = str(path_segments[0])
    messageID = int(path_segments[1])
    if is_number(chatID):
        chatID = int("-100"+chatID)  if  not chatID.startswith("-") else int(chatID)
        messageID = int(path_segments[1])
    if not is_number:
        channelData = await client.get_chat(chatID)
        chatID = channelData.id
    try:
        channelPeer = await client.resolve_peer(chatID)
        res = await client.invoke(GetMessagesViews(
            peer=channelPeer,
            id=[messageID],
            increment=True
            )
        )
        # if res: logger.debug(f"{phone_number} Viewed: {postLink}")
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
        logChannel(f"{phone_number}: Failed To Send Photo: {str(e)}")
        raise e

async def votePoll(task,client: Client,phone_number,self,taskID):
    chatID = "@"+task["chatID"] if not is_number(task["chatID"]) else int(task["chatID"])
    messageID = int(task["messageID"])
    try: 
        if str(chatID).startswith("-"): 
            if not await joinIfNot(client,chatID,task.get("inviteLink",None)): return
            await client.vote_poll(chatID,messageID,task["optionIndex"])
            logger.debug(f"Userbot {phone_number} voted on {chatID} with {task['optionIndex']}")
    except Exception as e: 
        logger.error(f"{phone_number} Failed To Vote: {str(e)}")
        raise e

async def sendMessage(task,client: Client,phone_number,self,taskID):
    textToDeliver = task['text']
    chatIDToDeliver = task['chatID']
    await client.send_message(chatIDToDeliver,textToDeliver)
    logger.debug(f"Message Delivered By: {phone_number}")

async def reactPost(task,client: Client,phone_number,self,taskID):
    postLink = task["postLink"].replace("/c","")
    parsed_url = urlparse(postLink)
    path_segments = parsed_url.path.strip("/").split("/")
    chatID = str(path_segments[0])
    messageID = int(path_segments[1])
    if is_number(chatID): chatID = int("-100"+chatID)  if  not chatID.startswith("-") else int(chatID)
    emojis = task['emoji']
    emojiString = random.choice(emojis)
    emoji = unicodedata.normalize("NFKC", emojiString)
    res = False
    try:
        res = await client.send_reaction(chatID,messageID,emoji=emoji)
    except ReactionInvalid:
        logChannel(f"{phone_number}: <b>[{emojiString}] Not Allowed</b> In <code>{chatID}</code>")
    except ChatWriteForbidden: pass
    except Exception as e: raise e
    # if res: logger.debug(f"Userbot {phone_number} reacted to {task['postLink']} with [{emojiString}]")

async def leaveVc(task,client: Client,phone_number,self,taskID):
    chatID = task["chatID"]
    try:
        app = PyTgCalls(client)
        await app.leave_call(chatID)
        logger.debug(f"{phone_number} had leaved the call.")
    except GroupcallForbidden: self.stopTask(taskID)
    except Exception as e: 
        logChannel("Error While Leaving Call: "+str(e),True)
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
        await app.start()
        await app.play(chat_id=chatID)
        logger.debug(f"{phone_number} joined the voice call and will leave after {finalDuration if finalDuration else "INFINITY"}s")
        if finalDuration:
            def leaveVc():
                try:asyncio.create_task(app.leave_call(chatID))
                except GroupcallForbidden: 
                    if self.tasksData.get(taskID,{}).get("canStop",True): self.stopTask(taskID)
                except Exception as e: raise e
        logger.debug(f"{phone_number} Leaved the call after {finalDuration}s")
        timer = Timer(float(finalDuration),leaveVc)
        timer.start()
    except ChannelInvalid:
        await client.join_chat(inviteLink)
        await self.add_task(phone_number,task)
    except UnMuteNeeded: 
        print(f"Error: UnmuteNeeded From {phone_number} While Joining Vc In {chatID}",True)
    except (ChatAdminRequired , GroupcallForbidden): 
        if self.tasksData.get(taskID,{}).get("canStop",True):
            logChannel(f"<b>Call Stopped From Channel: </b><code>{chatID}</code><b>  :   </b><code>{taskID}</code>. <b>Stopping Pending Tasks</b>")
            self.stopTask(taskID)
    except Exception as e: raise e

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
        await self.add_task(phone_number, task) 
    except PeerIdInvalid or ChannelPrivate or ChannelInvalid:
        logger.warning(f"{phone_number}: Invalid Peer ID for {chatID}. Retrying...")
        await joinIfNot(client,chatID,task.get("inviteLink",None))
        await self.add_task(phone_number, task)
    except Exception as e: 
        logChannel(f"{phone_number}: Failed To Report: {str(e)}",True)
        raise e

async def leaveChannel(task,client: Client,phone_number,self,taskID):
    for channel in task["channels"]:
        try:
            await client.leave_chat(channel if is_number(channel) else channel)
            logger.debug(f"Userbot {phone_number} leaved {channel}")
        except Exception as e:
            logger.error(f"Userbot {phone_number} failed to leave {channel}\nCause: {str(e)}")
            raise e

async def joinChannel(task,client: Client,phone_number,self,taskID):
    for channel in task["channels"]:
        try:
            if not is_number(channel):
                channelData = await client.get_chat(channel)
                channel = getattr(channelData,"id",channel)
            await client.join_chat(channel)
            logger.debug(f"Userbot {phone_number} joined {channel}")
        except UserAlreadyParticipant: pass
        except Exception as err: raise err
        await asyncio.sleep(task.get("restTime", 0))

async def mute_unmute(task,client: Client,phone_number,self,taskID):
    try:
        chatID = task["chatID"]
        # If Duration is 0 then channel will be unmuted
        foreverTime = 2147483647
        duration = task.get("duration",foreverTime) #Default number 2147483647 is for forever mute 
        finalDuration = duration if not isinstance(duration,list) else random.randint(int(duration[0]),int(duration[1]))
        channelInfo = await joinIfNot(client,chatID,task.get("inviteLink",None))
        async for dialog in client.get_dialogs():
            if dialog.chat.id == channelInfo.id: break
            channelPeer = await client.resolve_peer(channelInfo.id)
            mute_untill = (int(time.time()) + duration) if not duration == foreverTime else foreverTime
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
            if res:logger.debug(f"{phone_number} {"Muted" if duration else "Unmuted"} {chatID}")
    except Exception as err: raise err
