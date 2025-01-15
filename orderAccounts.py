from pyrogram import Client , filters
from config import USERBOT_SESSION
import asyncio 
from pytgcalls import PyTgCalls
from threading import Timer
from urllib.parse import urlparse
import random
from pyrogram.errors import *
from pyrogram.raw.functions.messages import GetMessagesViews
from database import Accounts , Channels
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message 
from pyrogram.raw.types import InputPeerChannel , InputReportReasonSpam
from pyrogram.raw.functions.messages import Report
from pyrogram.raw.functions.account import ReportPeer
from pyrogram.enums import ChatMemberStatus
from functions import *
import os

class OrderUserbotManager:
    def __init__(self, idle_timeout=300):
        self.clients = {}  # Active userbot instances
        self.task_queues = {}  # Task queues for each userbot
        self.idle_timers = {}  # Timers to stop inactive clients
        self.idle_timeout = idle_timeout
        self.syncBot = {}

    async def start_client(self,sessionString ,phone_number , isSyncBot=False):
        """Start or restart a userbot client."""
        if phone_number in self.clients:
            # Reset idle timer
            if not isSyncBot:self.reset_idle_timer(phone_number)
            return self.clients[phone_number]
        selected_proxy = random.choice(getProxies())
        proxy={
                "hostname": selected_proxy["host"],
                "port":int(selected_proxy["port"]),
                "username": selected_proxy["username"],
                "password": selected_proxy["password"],
                "scheme": "socks5"
            }
        client = Client(f"/{phone_number}",session_string=sessionString,phone_number=phone_number,proxy=proxy)
        oldSessionFile = USERBOT_SESSION+f"/{phone_number}"+'.session-journal'
        if os.path.exists(oldSessionFile):
            os.remove(oldSessionFile)
        try:
            await client.start()
            if isSyncBot: 
                self.syncBot = {
                    "client":client,
                    "phone_number":phone_number
                }
            self.clients[phone_number] = client
            print(f"Userbot {phone_number} started: {selected_proxy["host"]}:{selected_proxy['port']}")

            # Create task queue for the client
            if phone_number not in self.task_queues:
                self.task_queues[phone_number] = asyncio.Queue()

            # Process the task queue
            asyncio.create_task(self.process_task_queue(phone_number))

            # Set idle timer
            if not isSyncBot:self.reset_idle_timer(phone_number)

            return client
        except Exception as e:
            if "database is locked" in str(e) or "pyrogram.errors.SecurityCheckMismatch:" in str(e): print(str(e))
            elif "[401 AUTH_KEY_UNREGISTERED]" in str(e) or "[401 USER_DEACTIVATED_BAN]" in str(e) or "[401 SESSION_REVOKED]" in str(e): 
                print(f"Userbot {phone_number} Removed Please login again: {str(e)}")
                await self.stop_client(phone_number)
                Accounts.delete_one({"phone_number":str(phone_number)})
            elif "[406 AUTH_KEY_DUPLICATED]" in str(e):
                print(f"{phone_number} Duplicate Auth Key")
            else:
                print(f"Error starting userbot {phone_number}: {e}")
            return False

    async def stop_client(self, phone_number):
        """Stop a userbot client and clean up resources."""
        if phone_number in self.clients:
            await self.clients[phone_number].stop()
            del self.clients[phone_number]
            print(f"Userbot {phone_number} stopped.")

        # Clear task queue and idle timer
        if phone_number in self.task_queues:
            self.task_queues[phone_number].put_nowait(None)  # Sentinel to stop queue processing
            del self.task_queues[phone_number]
        if phone_number in self.idle_timers:
            self.idle_timers[phone_number].cancel()
            del self.idle_timers[phone_number]
    async def stop_all_client(self):
        clients_keys = list(self.clients.keys())
        for i in clients_keys:await self.stop_client(i)
    def reset_idle_timer(self, phone_number):
        """Reset or create an idle timer for a client."""
        if phone_number in self.idle_timers:
            self.idle_timers[phone_number].cancel()

        timer = Timer(self.idle_timeout, lambda: asyncio.run(self.stop_client(phone_number)))
        self.idle_timers[phone_number] = timer
        timer.start()

    async def process_task_queue(self, phone_number):
        """Process tasks for a specific userbot."""
        while True:
            task = await self.task_queues[phone_number].get()
            if task is None:break
            try:
                client = self.clients[phone_number]
                if task["type"] == "join_channel":
                    for channel in task["channels"]:
                        try:
                            await client.join_chat(channel)
                            print(f"Userbot {phone_number} joined {channel}")
                        except Exception as e:
                            if not "[400 USER_ALREADY_PARTICIPANT]" in str(e): print(f"Userbot {phone_number} failed to join {channel}\nCause: {str(e)}")
                        await asyncio.sleep(task.get("restTime", 0))
                elif task["type"] == "reportChannel":
                    chatID = task["chatID"]
                    try:
                        if str(chatID).startswith("-100"): await joinIfNot(client,chatID,task.get("inviteLink",None))
                        input_channel = await client.resolve_peer(str(chatID))
                        message_id = None
                        async for message in client.get_chat_history(chatID, limit=1):
                            message_id = message.id
                            break
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
                        await self.add_task(phone_number, task)  # Requeue the task
                    except Exception as e:
                        if "PEER_ID_INVALID" in str(e) or "[406 CHANNEL_PRIVATE]" in str(e) or "[400 CHANNEL_INVALID]" in str(e):
                            print(f"{phone_number}: Invalid Peer ID for {chatID}. Retrying...")
                            await client.join_chat(task["inviteLink"])  # Attempt to rejoin
                            await self.add_task(phone_number, task)  # Requeue the task
                        else:
                            print(f"{phone_number}: Failed To Report: {str(e)}")

                elif task["type"] == "leave_channel":
                    for channel in task["channels"]:
                        if phone_number == self.syncBot.get("phone_number"): continue
                        try:
                            await client.leave_chat(channel if is_number(channel) else channel)
                            print(f"Userbot {phone_number} leave {channel}")
                        except Exception as e:
                            print(f"Userbot {phone_number} failed to leave {channel}\nCause: {str(e)}")
                elif task["type"] == "joinVoiceChat":
                    chatID = task["chatID"]
                    inviteLink = task.get("inviteLink",None)
                    try:
                        app = PyTgCalls(client)
                        await app.start()
                        await app.play(chat_id=chatID)
                    except Exception as e:
                        if "[400 CHANNEL_INVALID]" in str(e):
                            await client.join_chat(inviteLink)
                            await self.add_task(phone_number,task)
                        else: print(str(e))
                elif task["type"] == "reactPost":
                    postLink = task["postLink"]
                    parsed_url = urlparse(postLink)
                    path_segments = parsed_url.path.strip("/").split("/")
                    chatID = str(path_segments[1])
                    messageID = int(path_segments[2])
                    if is_number(chatID):
                        chatID = int("-100"+path_segments[1])
                        messageID = int(path_segments[2])
                    emojis = task['emoji'] 
                    emoji = random.choice(emojis)
                    try:
                        await client.send_reaction(chatID,messageID,emoji=emoji)
                    except Exception as e:
                        if "[400 CHANNEL_INVALID]" in str(e) or "[406 CHANNEL_PRIVATE]" in str(e):
                            await client.join_chat(task["inviteLink"])
                            await client.send_reaction(chatID,messageID,emoji=emoji)
                        else: print(f"Failed To React: {str(e)}")
                    print(f"Userbot {phone_number} reacted to {task['postLink']} with {emoji}")
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
                    except Exception as e: print(f"{phone_number} Failed To Vote: {str(e)}")
                elif task["type"] == "viewPosts":
                    postLink = task["postLink"]
                    parsed_url = urlparse(postLink)
                    path_segments = parsed_url.path.strip("/").split("/")
                    chatID = str(path_segments[1])
                    messageID = int(path_segments[2])
                    if is_number(chatID):
                        chatID = int("-100"+path_segments[1])
                        messageID = int(path_segments[2])
                    try:
                        channelPeer = await client.resolve_peer(chatID)
                        await client.invoke(GetMessagesViews(
                            peer=channelPeer,
                            id=[messageID],
                            increment=True
                        ))
                    except Exception as e:
                        if ("[400 CHANNEL_INVALID]" in str(e)) or ("[406 CHANNEL_PRIVATE]" in str(e)):
                            await client.join_chat(task["inviteLink"])
                            channelPeer = await client.resolve_peer(chatID)
                            await client.invoke(GetMessagesViews(
                                peer=channelPeer,
                                id=[messageID],
                                increment=True
                            ))
                        else: print(f"Failed To View Post: {str(e)}")
            except Exception as e:
                if "[400 USER_ALREADY_PARTICIPANT]" in str(e): continue
                print(f"Error processing task for {phone_number}: {e}")
                raise e

            # Reset idle timer after completing a task
            if not phone_number == self.syncBot.get("phone_number"): self.reset_idle_timer(phone_number)

    async def add_task(self, phone_number, task):
        """Add a task to a userbot's queue."""
        if phone_number not in self.clients:
            print(f"Userbot {phone_number} not active. Starting...")
            await self.start_client(task["session_string"], phone_number)

        # Add task to the queue
        await self.task_queues[phone_number].put(task)

    async def bulk_order(self, userbots, task):
        """
        Send a bulk order to all userbots in the provided list.

        :param userbots: List of userbot details. Each detail is a dict with keys:
                         api_id, api_hash, phone_number, password.
        :param task: The task to execute (e.g., join_channel, leave_channel, etc.)
                     Example: {"type": "join_channel", "channel": "some_channel"}
        """
        taskLimit = 0
        for userbot in userbots:
            taskLimit += 1
            
            rest_time = task.get("restTime", 0)
            if isinstance(rest_time,list):rest_time = random.choice(rest_time)
            # Delay before executing the task
            if rest_time != 0:
                print(f"Resting for {rest_time} seconds before processing task for {userbot["phone_number"]}")
                await asyncio.sleep(rest_time)
            await self.add_task(
                phone_number=userbot["phone_number"],
                task={
                    **task,
                    "session_string": userbot["session_string"] ,
                },
            )
            # Break after order limit complete
            if taskLimit >= task["taskPerformCount"]: break
        print(f"Bulk order {task['type']} added for {len(userbots)} userbots.")
    async def addHandlersToSyncBot(self,needToJoin=True):
        try:
            syncBotData = Accounts.find_one({"syncBot":True})
            if not syncBotData: return print("Sync Bot Not Found")
            channels = list(Channels.find({}))
            if not len(channels): return 
            phone_number = syncBotData.get("phone_number")
            client = await self.start_client(syncBotData.get("session_string"),phone_number,isSyncBot=True)
            print("Sync Bot Trying to join Channels")
            channelsLink = []
            for i in channels: channelsLink.append(f"@{i.get("username")}" if i.get("username",False) else i.get("inviteLink"))
            from syncerBotHandler import messageHandler  
            client.add_handler(MessageHandler(messageHandler))
            for channel in channelsLink:
                chat = await client.get_chat(channel)
                chatStatus = None
                try: 
                    chatMember = await client.get_chat_member(chat.id, "me")
                    chatStatus = chatMember.status
                except Exception as e: 
                    if "[400 USER_NOT_PARTICIPANT]" in str(e): chatStatus = ChatMemberStatus.LEFT
                    else: raise e
                if needToJoin and not (chatStatus in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR , ChatMemberStatus.OWNER]): 
                    await self.add_task(phone_number,{
                    "type": "join_channel",
                    "channels": [channel],
                    "restTime": 1,
                    "session_string": syncBotData.get("session_string")
                })
        except FloodWait as e:
            print(f"SyncBot Flood Wait: {e.value} seconds")
            await asyncio.sleep(e.value)
            await self.addHandlersToSyncBot()
    def getSyncBotClient(self):
        if "client" in self.syncBot: return self.syncBot["client"]
        else: print("Sync Bot Not Found")
    

UserbotManager = OrderUserbotManager()