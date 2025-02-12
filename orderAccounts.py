from pyrogram import Client , filters
from pytgcalls import filters as callFilters
from config import USERBOT_SESSION
import asyncio 
from pytgcalls import PyTgCalls
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

class OrderUserbotManager:
    def __init__(self, idle_timeout=360):
        self.clients = {}
        self.task_queues = {}
        self.idle_timers = {}
        self.idle_timeout = idle_timeout
        self.syncBot = {}
        self.sessionStrings = {}
        self.syncBotHandlersData = {}

    async def start_client(self,sessionString ,phone_number , isSyncBot=False):
        if phone_number in self.clients:
            # Reset idle timer
            if not isSyncBot:self.reset_idle_timer(phone_number)
            else: await self.addHandlersToSyncBot(True)
            return self.clients[phone_number]
        accoundData = Accounts.find_one({"phone_number":phone_number})
        proxyDetail = accoundData.get("proxy",None)
        proxy = None
        ip = None
        port = None
        if proxyDetail:
            ip , port , username , password = proxyDetail.split(":")
            proxy= {
                "hostname": ip,
                "port":int(port),
                "username": username,
                "password": password,
                "scheme": "socks5"
            }
        client = Client(f"/{phone_number}",session_string=sessionString,phone_number=phone_number,proxy=proxy,in_memory=True)
        oldSessionFile = USERBOT_SESSION+f"/{phone_number}"+'.session-journal'
        if os.path.exists(oldSessionFile):
            os.remove(oldSessionFile)
        try:
            self.clients[phone_number] = client
            await client.start()
            self.sessionStrings[phone_number] = sessionString
            print(f"Userbot {phone_number} started: {(ip+":"+port) if proxyDetail else "Without Proxy"}")
            if phone_number not in self.task_queues: self.task_queues[phone_number] = asyncio.Queue()
            asyncio.create_task(self.process_task_queue(phone_number))
            if not isSyncBot: self.reset_idle_timer(phone_number)
            if isSyncBot: 
                self.syncBot = {
                    "client":client,
                    "phone_number":phone_number
                }
                await self.addHandlersToSyncBot(True,client=client)
            return client
        except AuthKeyDuplicated:
            logChannel(f"{phone_number} Duplicate Auth Key: Account Removed")
            await self.stop_client(phone_number)
            Accounts.delete_one({"phone_number":str(phone_number)})
        except (AuthKeyUnregistered,SessionRevoked):
            logChannel(f"Account Removed: {phone_number} Please login again: {str(e)}")
            await self.stop_client(phone_number)
            Accounts.delete_one({"phone_number":str(phone_number)})
        except (UserDeactivated,UserDeactivatedBan):
            logChannel(f"Account [{phone_number}]: Banned")
            await self.stop_client(phone_number)
            Accounts.delete_one({"phone_number":str(phone_number)})
        except Exception as e:
            del self.clients[phone_number]
            if "database is locked" in str(e) or "pyrogram.errors.SecurityCheckMismatch:" in str(e): print(str(e))
            logChannel(f"Error starting userbot {phone_number}: {e}")
            return False

    async def stop_client(self, phone_number):
        try:
            if phone_number in self.clients:
                client = self.clients[phone_number]
                if client.is_initialized: await client.stop()
                elif client.is_connected: await client.disconnect()
                del self.clients[phone_number]
                print(f"Userbot {phone_number} stopped.")
            if phone_number == self.syncBot.get("phone_number"):self.syncBotHandlersData[phone_number] = []
            if phone_number in self.task_queues:
                self.task_queues[phone_number].put_nowait(None)
                del self.task_queues[phone_number]
            if phone_number in self.idle_timers:
                self.idle_timers[phone_number].cancel()
                del self.idle_timers[phone_number]
        except Exception as e: logChannel(f"Error while stopping {phone_number}: {str(e)}")
    async def stop_all_client(self):
        clients_keys = list(self.clients.keys())
        for i in clients_keys:await self.stop_client(i)
        return False
    def reset_idle_timer(self, phone_number):
        if phone_number in self.idle_timers:
            self.idle_timers[phone_number].cancel()
        timer = Timer(self.idle_timeout, lambda: asyncio.run(self.stop_client(phone_number)))
        self.idle_timers[phone_number] = timer
        timer.start()
    
    async def process_task_queue(self, phone_number):
        while True:
            task = await self.task_queues[phone_number].get()
            if task is None:break
            client: Client = self.clients[phone_number]
            if phone_number == self.syncBot.get("phone_number"): continue
            try:
                if task["type"] == "join_channel":
                    for channel in task["channels"]:
                        try:
                            if not is_number(channel):
                                channelData = await client.get_chat(channel)
                                channel = getattr(channelData,"id",channel)
                            await client.join_chat(channel)
                            print(f"Userbot {phone_number} joined {channel}")
                        except UserAlreadyParticipant: pass
                        except Exception as e: 
                            logChannel(f"Userbot {phone_number} failed to join {channel}\nCause: {str(e)}")
                            raise e
                        await asyncio.sleep(task.get("restTime", 0))
                elif task["type"] == "changeNotifyChannel":
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
                        if res:print(f"{phone_number} {"Muted" if duration else "Unmuted"} {chatID}")
                    except Exception as err:
                        logChannel(f"Error While Trying To {"Mute" if duration else "Unmute"} {chatID} from {phone_number}: {err}")
                        raise e
                elif task["type"] == "reportChannel":
                    chatID = task["chatID"]
                    try:
                        if str(chatID).startswith("-100"): await joinIfNot(client,chatID,task.get("inviteLink",None))
                        input_channel = await client.resolve_peer(str(chatID))
                        res = await client.invoke(
                            ReportPeer(
                                peer=input_channel,
                                message="Spam",
                                reason=InputReportReasonSpam()
                            )
                        )
                        print(f"Userbot {phone_number} reported {chatID}: {res}")
                    except FloodWait as e:
                        print(f"{phone_number}: Flood Wait: {e.value} seconds")
                        await asyncio.sleep(e.value)
                        await self.add_task(phone_number, task) 
                    except PeerIdInvalid or ChannelPrivate or ChannelInvalid:
                        print(f"{phone_number}: Invalid Peer ID for {chatID}. Retrying...")
                        await client.join_chat(task["inviteLink"])
                        await self.add_task(phone_number, task)
                    except Exception as e: 
                        logChannel(f"{phone_number}: Failed To Report: {str(e)}")
                        raise e

                elif task["type"] == "leave_channel":
                    for channel in task["channels"]:
                        if phone_number == self.syncBot.get("phone_number"): continue
                        try:
                            await client.leave_chat(channel if is_number(channel) else channel)
                            print(f"Userbot {phone_number} leaved {channel}")
                        except Exception as e:
                            print(f"Userbot {phone_number} failed to leave {channel}\nCause: {str(e)}")
                            raise e
                elif task["type"] == "joinVoiceChat":
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
                        print(f"{phone_number} joined the voice call and will leave after {finalDuration if finalDuration else "INFINITY"}s")
                        if finalDuration:
                            def leaveVc():
                                try:asyncio.create_task(app.leave_call(chatID))
                                except Exception as e: raise e
                                print(f"{phone_number} Leaved the call after {finalDuration}s")
                            timer = Timer(float(finalDuration),leaveVc)
                            timer.start()
                    except ChannelInvalid:
                        await client.join_chat(inviteLink)
                        await self.add_task(phone_number,task)
                    except Exception as e: print(str(e))
                elif task["type"] == "leaveVoiceChat":
                    chatID = task["chatID"]
                    try:
                        app = PyTgCalls(client)
                        await app.leave_call(chatID)
                        print(f"{phone_number} had leaved the call.")
                    except Exception as e: 
                        logChannel("Error While Leaving Channel: "+str(e))
                        raise e
                elif task["type"] == "reactPost":
                    postLink = task["postLink"].replace("/c","")
                    parsed_url = urlparse(postLink)
                    path_segments = parsed_url.path.strip("/").split("/")
                    chatID = str(path_segments[0])
                    messageID = int(path_segments[1])
                    if is_number(chatID):
                        chatID = int("-100"+path_segments[0])
                        messageID = int(path_segments[1])
                    emojis = task['emoji']
                    emojiString = random.choice(emojis)
                    emoji = unicodedata.normalize("NFKC", emojiString)
                    res = False
                    try:
                        res = await client.send_reaction(chatID,messageID,emoji=emoji)
                    except ChannelInvalid or ChannelPrivate:
                        await client.join_chat(task["inviteLink"])
                        res = await client.send_reaction(chatID,messageID,emoji=emoji)
                    except FloodWait as e:
                        print(f"Flood wait for {phone_number}: Sleeping for {e.value} seconds")
                        await asyncio.sleep(e.value)
                        await self.add_task(phone_number, task)
                    except Exception as e: 
                        logChannel(f"{phone_number} Failed To React [{emojiString}]: {str(e)}")
                        raise e
                    if res: print(f"Userbot {phone_number} reacted to {task['postLink']} with [{emojiString}]")
                elif task['type'] == 'sendMessage':
                    textToDeliver = task['text']
                    chatIDToDeliver = task['chatID']
                    await client.send_message(chatIDToDeliver,textToDeliver)
                    print(f"Message Delivered By: {phone_number}")
                elif task['type'] == "votePoll":
                    chatID = "@"+task["chatID"] if not is_number(task["chatID"]) else int(task["chatID"])
                    messageID = int(task["messageID"])
                    try: 
                        if str(chatID).startswith("-100"): 
                            if not await joinIfNot(client,chatID,task.get("inviteLink",None)): return
                        await client.vote_poll(chatID,messageID,task["optionIndex"])
                        print(f"Userbot {phone_number} voted on {chatID} with {task['optionIndex']}")
                    except Exception as e: 
                        print(f"{phone_number} Failed To Vote: {str(e)}")
                        raise e
                elif task['type'] == 'sendPhoto':
                    photoLink = task['photoLink']
                    chatIDToDeliver = task['chatID']
                    chat_username, message_id = photoLink.split('/')[-2:]
                    message_id = int(message_id)
                    try:
                        fileChat = await client.get_chat(chat_username)
                        message = await client.get_messages(fileChat.id, message_id)
                        fileID = message.photo.file_id
                        await client.send_photo(chat_id=chatIDToDeliver, photo=fileID)
                        print(f"Photo Delivered To {chatIDToDeliver} By: {phone_number}")
                    except UserNotParticipant:
                        print(f"User {phone_number} Not Participant In {chatIDToDeliver}")
                        await client.join_chat(chat_username)
                    except FloodWait as e:
                        print(f"Flood wait for {phone_number}: Sleeping for {e.value} seconds")
                        await asyncio.sleep(e.value) 
                        continue
                    except Exception as e:
                        logChannel(f"{phone_number}: Failed To Send Photo: {str(e)}")
                        raise e
                elif task["type"] == "viewPosts":
                    postLink = task["postLink"].replace("/c","")
                    parsed_url = urlparse(postLink)
                    path_segments = parsed_url.path.strip("/").split("/")
                    chatID = str(path_segments[0])
                    messageID = int(path_segments[1])
                    if is_number(chatID):
                        chatID = int("-100"+path_segments[0])
                        messageID = int(path_segments[1])
                    try:
                        channelPeer = await client.resolve_peer(chatID)
                        res = await client.invoke(GetMessagesViews(
                            peer=channelPeer,
                            id=[messageID],
                            increment=True
                        ))
                        if res: print(f"{phone_number} Viewed: {postLink}")
                    except ChannelInvalid or ChannelPrivate:
                        await joinIfNot(client,chatID,task["inviteLink"])
                        await self.add_task(phone_number,task)
                    except Exception as e: 
                        logChannel(f"{phone_number} Failed To View Post: {str(e)}")
                        raise e
            except UserAlreadyParticipant: pass
            except MessageIdInvalid: pass
            except (ConnectionError,ConnectionAbortedError,RPCError,OSError) as e:
                logChannel(f"Connection Error {phone_number}: {str(e)}. Restarting..")
                await self.stop_client(phone_number)
                await self.start_client(task["session_string"], phone_number)
                await self.add_task(phone_number,task)
            except (AuthKeyUnregistered,SessionRevoked):
                logChannel(f"Account Removed: {phone_number} Please login again: {str(e)}")
                await self.stop_client(phone_number)
                Accounts.delete_one({"phone_number":str(phone_number)})
            except (UserDeactivated,UserDeactivatedBan):
                logChannel(f"Account [{phone_number}]: Banned")
                await self.stop_client(phone_number)
                Accounts.delete_one({"phone_number":str(phone_number)})
            except Exception as e: 
                if "closed database" in str(e): 
                    logChannel(f"Closed Database Error: {phone_number}. Restarting...")
                    await self.stop_client(phone_number)
                    await self.start_client(task["session_string"], phone_number)
                    await self.add_task(phone_number,task)
                    continue
                del task["session_string"]
                import traceback
                logChannel(f"Stack Trace: {traceback.format_exc()}")
                logChannel(f"Error processing task for {phone_number}: <b>{e}</b>\nType: {type(e)}\n\nTask Details: <code>{format_json(task)}</code>")

            # Reset idle timer after completing a task
            if not phone_number == self.syncBot.get("phone_number"): self.reset_idle_timer(phone_number)

    async def add_task(self, phone_number, task):
        if phone_number not in self.clients:
            print(f"Userbot {phone_number} not active. Starting...")
            if not await self.start_client(task["session_string"], phone_number): return
        if not phone_number in self.task_queues: self.task_queues[phone_number] = asyncio.Queue()
        await self.task_queues[phone_number].put(task)

    async def bulk_order(self, userbots, task):
        taskLimit = 0
        tasksGathering = []
        taskPerformCount = random.choice(task["taskPerformCount"]) if isinstance(task["taskPerformCount"],list) else task["taskPerformCount"]
        for userbot in userbots:
            taskLimit += 1
            rest_time = task.get("restTime", 0)
            if isinstance(rest_time,list) and len(rest_time) > 1:rest_time = random.randint(int(rest_time[0]),int(rest_time[1]))
            elif isinstance(rest_time,list) and len(rest_time) == 1: rest_time = rest_time[0]
            if rest_time != 0:
                print(f"Resting for {rest_time} seconds before processing task for {userbot["phone_number"]}")
                await asyncio.sleep(float(rest_time))
                await self.add_task(
                    phone_number=userbot["phone_number"],
                    task={
                        **task,
                        "session_string": userbot["session_string"] ,
                    },
                )
            elif rest_time == 0:
                tasksGathering.append(self.add_task(
                    phone_number=userbot["phone_number"],
                    task={
                        **task,
                        "session_string": userbot["session_string"] ,
                    },))
            if taskLimit >= int(taskPerformCount) : break
        await asyncio.gather(*tasksGathering)
        logChannel(f"Bulk order {task['type']} added for {len(userbots)} userbots.")
    async def addHandlersToSyncBot(self,needToJoin=True,client: Client|None = None):
        try:
            syncBotData = Accounts.find_one({"syncBot":True})
            if not syncBotData: return logChannel("Sync Bot Not Found")
            channels = list(Channels.find({}))
            if not len(channels): return 
            phone_number = syncBotData.get("phone_number")
            if not client: client = await self.start_client(syncBotData.get("session_string"),phone_number,isSyncBot=True)
            if client.is_connected and not client.is_initialized: await client.disconnect()
            if not client.is_initialized:await client.start()
            channelsLink = []
            for i in channels: channelsLink.append(f"@{i.get("username")}" if i.get("username",False) else i.get("inviteLink"))
            from syncerBotHandler import messageHandler , voiceChatHandler
            if not client:
                return logChannel(f"{phone_number}  SyncBot Failed To Run")
            if phone_number in self.syncBotHandlersData: 
                for i in self.syncBotHandlersData[phone_number]: 
                    try: client.remove_handler(i)
                    except: pass
                    self.syncBotHandlersData.remove(i)
            try: 
                self.syncBotHandlersData[phone_number] = []
                self.syncBotHandlersData[phone_number].append(client.add_handler(MessageHandler(messageHandler)))
                self.syncBotHandlersData[phone_number].append(client.add_handler(RawUpdateHandler(voiceChatHandler)))
            except:pass
            logChannel(f"Handlers added for syncBot")
            for channel in channelsLink:
                chatStatus = None
                try: 
                    chat = await client.get_chat(channel)
                    chatMember = await client.get_chat_member(chat.id, "me")
                    chatStatus = chatMember.status
                except UserNotParticipant: chatStatus = ChatMemberStatus.LEFT
                except Exception as e: print(str(e))
                if needToJoin and not (chatStatus in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR , ChatMemberStatus.OWNER]): 
                    await self.add_task(phone_number,{
                    "type": "join_channel",
                    "channels": [channel],
                    "restTime": 1,
                    "session_string": syncBotData.get("session_string")
                })
                
                while True:
                    try:
                        await asyncio.sleep(100)
                        if not client.is_connected or not client.is_initialized: 
                            logChannel(f"SyncBot {phone_number} is Disconnected. Trying to restart...")
                            await self.addHandlersToSyncBot(needToJoin,client)
                        else: print(f"SyncBot {phone_number} is Running.....") 
                    except: logChannel(f"Error While Restarting SyncBot: {str(e)}")
        except FloodWait as e:
            logChannel(f"SyncBot Flood Wait: {e.value} seconds")
            await asyncio.sleep(e.value)
            await self.addHandlersToSyncBot(needToJoin,client)
        except Exception as e: print(str(e))
    def getSyncBotClient(self):
        if "client" in self.syncBot: return self.syncBot["client"]
        else: 
            print("Sync Bot Not Found")
            return None

    

UserbotManager = OrderUserbotManager()