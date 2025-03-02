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
from methods import *


class OrderUserbotManager:
    def __init__(self):
        self.clients = {}
        self.task_queues = {}
        self.idle_timers = {}
        self.idle_timeout = 360
        self.syncBot = {}
        self.sessionStrings = {}
        self.syncBotHandlersData = {}
        self.tasksData = {}
    async def start_client(self,sessionString ,phone_number , isSyncBot=False):
        if phone_number in self.clients:
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
            isProxyWorking = checkProxy(ip,port,username,password)
            if isProxyWorking:
                proxy= {
                    "hostname": ip,
                    "port":int(port),
                    "username": username,
                    "password": password,
                    "scheme": "socks5"
                }
            else:
                logChannel(
                    string=f"<b>{phone_number}:</b> Failed To Connect To Proxy <code>{ip}</code>:<code>{port}</code>\nStarting Without Using Proxy",
                    keyboard={"inline_keyboard":
                                [
                                    [
                                        {"text":"🗑 Remove Proxy","callback_data":f"/removeProxy {phone_number}"}
                                    ]
                                ] 
                        },
                    isError=True)

        client = Client(f"/{phone_number}",session_string=sessionString,phone_number=phone_number,proxy=proxy)
        oldSessionFile = USERBOT_SESSION+f"/{phone_number}"+'.session-journal'
        if os.path.exists(oldSessionFile):
            os.remove(oldSessionFile)
        try:
            self.clients[phone_number] = client
            if isSyncBot:await client.start()
            else: await client.connect()
            self.sessionStrings[phone_number] = sessionString
            # logger.info(f"Userbot {phone_number} started: {(ip+":"+port) if proxyDetail else "Without Proxy"}")
            await client.send_message("me","Ping!")
            if phone_number not in self.task_queues: 
                self.task_queues[phone_number] = asyncio.Queue()
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
            logChannel(f"{phone_number} Duplicate Auth Key: Account Removed",True)
            await self.stop_client(phone_number)
            Accounts.delete_one({"phone_number":str(phone_number)})
        except (AuthKeyUnregistered,SessionRevoked) as e:
            logChannel(f"Account Removed: {phone_number} Please login again: {str(e)}")
            await self.stop_client(phone_number)
            Accounts.delete_one({"phone_number":str(phone_number)})
        except (UserDeactivated,UserDeactivatedBan):
            logChannel(f"Account [{phone_number}]: Banned")
            await self.stop_client(phone_number)
            Accounts.delete_one({"phone_number":str(phone_number)})
        except Exception as e:
            if phone_number in self.clients:
                del self.clients[phone_number]
    
            if "database is locked" in str(e) or "pyrogram.errors.SecurityCheckMismatch:" in str(e): 
                logger.warning(f"Database Locked Error While Starting [{phone_number}]")
                raise e 
    
            logChannel(f"Error starting userbot {phone_number}: {e}", True) 
            return False  

    async def stop_client(self, phone_number):
        try:
            if phone_number in self.clients:
                client = self.clients[phone_number]
                del self.clients[phone_number]
                try:
                    if client.is_initialized: await client.stop()
                    elif client.is_connected: await client.disconnect()
                    # logger.warning(f"Userbot {phone_number} stopped.")
                except Exception as err:
                    logger.critical(f"Error While Disconnecting [{phone_number}]: <b>{type(err)}</b><code>{err}</code>")
                
            if phone_number == self.syncBot.get("phone_number"):self.syncBotHandlersData[phone_number] = []
            if phone_number in self.task_queues:
                self.task_queues[phone_number].put_nowait(None)
                del self.task_queues[phone_number]

            if phone_number in self.idle_timers:
                self.idle_timers[phone_number].cancel()
                del self.idle_timers[phone_number]
        except Exception as e: logChannel(f"Error While Removing [{phone_number}]: <b>{type(err)}</b><code>{err}</code>")
    async def stop_all_client(self):
        clients_keys = list(self.clients.keys())
        for phone_number in clients_keys:
            await self.stop_client(phone_number)  # Stop all userbots
            self.clients.clear()  # Ensure all clients are removed
            self.task_queues.clear()  # Clear task queues
            self.idle_timers.clear()  # Cancel all idle timers
        return True

    def reset_idle_timer(self, phone_number):
        if phone_number in self.idle_timers:
            self.idle_timers[phone_number].cancel()
        self.idle_timers[phone_number] = asyncio.create_task(self._idle_timeout_handler(phone_number))
    
    async def _idle_timeout_handler(self, phone_number):
        try:
            await asyncio.sleep(self.idle_timeout)
            await self.stop_client(phone_number)
        except: pass
    
    async def process_task_queue(self, phone_number):
        while True:
            if phone_number not in self.task_queues:
                logger.error(f"Task queue for {phone_number} not found.")
                break
            task = await self.task_queues[phone_number].get()
            if task is None:
                break
            taskID = task.get("taskID",None)
            client: Client = self.clients[phone_number]
            if phone_number == self.syncBot.get("phone_number"): continue
            if not client.is_connected: 
                logger.critical(f"{phone_number}: Not Running While Performing Tasks")
                continue
            tasks = []
            try:
                methods = {
                    "join_channel": joinChannel,
                    "changeNotifyChannel": mute_unmute,
                    "reportChannel": reportChat,
                    "leave_channel": leaveChannel,
                    "joinVoiceChat": joinVc,
                    "leaveVoiceChat": leaveVc,
                    "reactPost": reactPost,
                    "sendMessage": sendMessage,
                    "sendPhoto": sendPhoto,
                    "votePoll": votePoll,
                    "viewPosts": viewPost
                }
                method = methods[task.get("type")]
                tasks.append(asyncio.create_task(method(phone_number=phone_number, task=task, client=client, taskID=taskID, self=self)))
                await asyncio.gather(*tasks)  # Run all tasks in parallel
            except (ChannelInvalid,ChannelPrivate,PeerIdInvalid , UserNotParticipant) as e:
                inviteLink = task.get("inviteLink",None)
                if not inviteLink:
                  return logChannel(f"<b>No Any Invite Link Found For </b><code>{task.get("chat_id",None)}</code> \nPlease Remove and Add This channel again")
                logChannel(f"<b>{phone_number}</b>: Need to <b><a href='{task.get("inviteLink",None)}'>{task.get('inviteLink')}</a></b> To View.\nError: <code>{e}</code>\n\n Joining and Trying Again....")
                await joinIfNot(client,None,inviteLink)
                await self.add_task(phone_number, task)
                continue
            except UserAlreadyParticipant: pass
            except MessageIdInvalid: 
                if self.tasksData.get(taskID,{}).get("canStop",True):
                    logChannel(f"<b>Message Deleted, Stopping Task</b>")
                    self.stopTask(taskID)
            except BotMethodInvalid:
                logChannel(f"Telegram Considering <b>{phone_number}</b> as Bot. <b>Account Removed</b>")
                await self.stop_client(phone_number)
                Accounts.delete_one({"phone_number":str(phone_number)})
                continue
            except (ConnectionError,ConnectionAbortedError,OSError) as e:
                logChannel(f"Connection Error {phone_number}: {str(e)}. \n\nType: {type(e)}\n\n <b>Restarting..</b>")
                await self.stop_client(phone_number)
                await self.start_client(task["session_string"], phone_number)
                await self.add_task(phone_number,task)
            except (AuthKeyUnregistered,SessionRevoked) as e:
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
                    if not client.is_connected: await client.connect()
                    else:
                        await self.stop_client(phone_number)
                        await self.start_client(task["session_string"], phone_number)
                    await self.add_task(phone_number,task)
                    continue
                del task["session_string"]
                import traceback
                logChannel(f"Stack Trace: {traceback.format_exc()}")
                logChannel(f"Error processing task for {phone_number}: <b>{e}</b>\nType: {type(e)}\n\nTask Details:\n{format_json(task)}")

            # Reset idle timer after completing a task
            if not phone_number == self.syncBot.get("phone_number"): self.reset_idle_timer(phone_number)
    def stopTask(self,taskID):
        if taskID in self.tasksData: del self.tasksData[taskID]
    async def add_task(self, phone_number, task):
        if phone_number not in self.clients:
            # logger.warning(f"Userbot {phone_number} not active. Starting...")
            if not await self.start_client(task["session_string"], phone_number): return
        if not phone_number in self.task_queues: self.task_queues[phone_number] = asyncio.Queue()
        await self.task_queues[phone_number].put(task)
    
    async def bulk_order(self, userbots, task):
        taskLimit = 0
        tasksGathering = []
        taskPerformCount = random.choice(task["taskPerformCount"]) if isinstance(task["taskPerformCount"],list) else task["taskPerformCount"]
        taskID = generateRandomString(10)
        task["taskID"] = taskID 
        self.tasksData[taskID] = task
        for userbot in userbots:
            if not (taskID in self.tasksData): 
                logChannel(f"<b>Task Deleted: </b><code>{taskID}</code>")
                break
            taskLimit += 1
            rest_time = task.get("restTime", 0)
            if isinstance(rest_time,list) and len(rest_time) > 1:rest_time = random.randint(int(rest_time[0]),int(rest_time[1]))
            elif isinstance(rest_time,list) and len(rest_time) == 1: rest_time = rest_time[0]
            if rest_time != 0:
                self.tasksData[taskID]["canStop"] = True
                logger.debug(f"Resting for {rest_time} seconds before processing task for {userbot["phone_number"]}")
                await asyncio.sleep(float(rest_time))
                await self.add_task(
                    phone_number=userbot["phone_number"],
                    task={
                        **task,
                        "session_string": userbot["session_string"] ,
                    },
                )
            elif rest_time == 0:
                self.tasksData[taskID]["canStop"] = False
                tasksGathering.append(self.add_task(
                    phone_number=userbot["phone_number"],
                    task={
                        **task,
                        "session_string": userbot["session_string"] ,
                    },))
            if taskLimit >= int(taskPerformCount) : break
        # if taskID in self.tasksData: logChannel(f"Bulk order {task['type']} added for {len(userbots)} userbots.\n\n{format_json(task)}")
        await asyncio.gather(*tasksGathering)
        
    async def addHandlersToSyncBot(self,needToJoin=True,client: Client|None = None):
        try:
            syncBotData = Accounts.find_one({"syncBot":True})
            if not syncBotData: return logChannel("Sync Bot Not Found")
            channels = list(Channels.find({}))
            if not len(channels): return 
            phone_number = syncBotData.get("phone_number")
            if not client: client = await self.start_client(syncBotData.get("session_string"),phone_number,isSyncBot=True)
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
            except Exception as e:logger.critical(f"Error adding Handler To SyncBot: {e}")
            logChannel("<b>✅ Handlers registered for SyncBot!</b>")
            for channel in channelsLink:
                chatStatus = None
                try: 
                    chat = await client.get_chat(channel)
                    chatMember = await client.get_chat_member(chat.id, "me")
                    chatStatus = chatMember.status
                except UserNotParticipant: chatStatus = ChatMemberStatus.LEFT
                except UsernameNotOccupied: 
                    logChannel(f"{channel} Is Invalid. Removing it from Bot.",isError=True)
                    Channels.delete_one({"username":channel.replace("@","")})
                    Channels.delete_one({"inviteLink": channel})
                except Exception as e: 
                    raise e
                if needToJoin and not (chatStatus in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR , ChatMemberStatus.OWNER]): 
                    await self.add_task(phone_number,{
                    "type": "join_channel",
                    "channels": [channel],
                    "restTime": 1,
                    "session_string": syncBotData.get("session_string"),
                })
                asyncio.create_task(self.keepRunningSyncBot(phone_number,client))
        except FloodWait as err:
            logChannel(f"SyncBot Flood Wait: {err.value} seconds")
            await asyncio.sleep(err.value)
            await self.addHandlersToSyncBot(needToJoin,client)
        except Exception as err: 
            logChannel(f"<b>Error</b> In SyncBot Handler: <code>{str(err)}</code>",isError=True)
    async def keepRunningSyncBot(self,phone_number,client:Client):
        while True:
            try:
                await asyncio.sleep(100)
                if not client.is_connected or not client.is_initialized: 
                    logChannel(f"SyncBot {phone_number} is Disconnected. Trying to restart...",isError=True)
                    await self.stop_client(phone_number)
                    await self.addHandlersToSyncBot(None)
                else: logger.info(f"SyncBot {phone_number} is Running.....") 
            except Exception as e: logger.warning(f"Error While Restarting SyncBot: {str(e)}")
    def getSyncBotClient(self):
        if "client" in self.syncBot: return self.syncBot["client"]
        else: 
            logger.warning("Sync Bot Not Found")
            return None

    

UserbotManager = OrderUserbotManager()