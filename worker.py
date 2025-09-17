from pyrogram import Client
from config import *
from pathlib import Path
from logger import logger
import json, os, asyncio, aiofiles, sys
from database import *
from methods import *
from functions import safe_create_task

worker_id = None
ACCOUNT_PATH = "accounts"
workers = {}

class Worker:
    def __init__(self, phone_number: str, account_data: dict):
        self.phone_number = phone_number
        self.accountData = account_data
        self.is_running = True
        self.client: Client = Client(
            phone_number,
            session_string=self.accountData.get("session_string"),
            api_id=API_ID,
            api_hash=API_HASH,
            max_message_cache_size=100,
            max_concurrent_transmissions=1
        )

    async def start(self):
        try:
            accountData = self.accountData
            await self.client.start()
            # logger.debug(f"[{self.phone_number}]: Started")
            safe_create_task(self.monitor_tasks())
            # if not accountData.get("syncBot", False) and not accountData.get("helperBot", False): asyncio.create_task(cleanup(self.client,self.phone_number))
        except (AuthKeyUnregistered,SessionRevoked,AuthKeyDuplicated) as e:
            await logChannel(f"Account Removed: {self.phone_number} Please login again: {str(e)}")
            Accounts.delete_one({"phone_number":str(self.phone_number)})
            await self.stop()
        except (UserDeactivated,UserDeactivatedBan):
            await logChannel(f"Account [{self.phone_number}]: Banned")
            Accounts.delete_one({"phone_number":str(self.phone_number)})
            await self.stop()
        except SessionPasswordNeeded: 
            await self.client.connect()
            try: await self.client.check_password("7890" or self.accountData.get("password"))
            except Exception as e: logger.error(f"Failed to check password for {self.phone_number}: {e}")
            await self.client.disconnect()
            await self.client.start()
        except Exception as e:
            logger.error(f"[{self.phone_number}] Failed to connect: {e}")
            raise e

    async def stop(self):
        try:
            await self.client.stop()
            if self.phone_number in workers: del workers[self.phone_number]
            self.is_running = False
        except Exception as e:
            logger.error(f"[{self.phone_number}] Failed to disconnect: {e}")

    async def restart_self(self):
        logger.warning(f"[{self.phone_number}]: Restarting worker... (attempting reconnect first)")
        backoffs = [1, 3, 10]
        for attempt, delay in enumerate(backoffs, start=1):
            try:
                logger.debug(f"[{self.phone_number}] Reconnect attempt {attempt}/{len(backoffs)}")
                try:
                    await self.client.stop()
                except Exception:
                    pass
                await asyncio.sleep(delay)
                await self.client.start()
                # if connected, keep running with the same worker
                if getattr(self.client, "is_connected", True):
                    logger.info(f"[{self.phone_number}] Reconnected successfully on attempt {attempt}")
                    return
            except Exception as e:
                logger.warning(f"[{self.phone_number}] Reconnect attempt {attempt} failed: {e}")

        # If reconnect attempts failed, recreate the worker cleanly
        logger.warning(f"[{self.phone_number}]: Reconnect attempts failed — recreating worker")
        await self.stop()
        acc_file = os.path.join(ACCOUNT_FOLDER, self.phone_number, "account.json")
        if os.path.exists(acc_file):
            with open(acc_file) as af:
                acc_data = json.load(af)
            new_worker = Worker(self.phone_number, acc_data)
            await new_worker.start()
            workers[self.phone_number] = new_worker

    async def monitor_tasks(self):
        tasks_folder = f"{ACCOUNT_FOLDER}/{self.phone_number}/tasksData"
        os.makedirs(tasks_folder, exist_ok=True)
        while True:
            if not self.is_running: break
            try:
                accountsData = os.path.join(WORKERS_DIR,worker_id,"accounts.json")
                if os.path.exists(accountsData):
                    with open(accountsData,'r') as file:
                        data = json.load(file)
                        if not (self.phone_number in data):
                            await self.stop()
                            break
            except Exception as error: logger.error(f"[{self.phone_number}]: Failed to open accounts.json: {str(error)}")
            try:
                files = [f for f in os.listdir(tasks_folder) if f.endswith(".json")]
                retries = {}
                for file in files:
                    path = os.path.join(tasks_folder, file)
                    # logger.debug(f"[{self.phone_number}]: {file}")
                    async with aiofiles.open(path, "r") as f:
                        content = await f.read()
                    if not content.strip():
                        continue
                    task = json.loads(content)
                    # logger.debug(f"[{self.phone_number}]: {file}")
                    safe_create_task(self.add_task(task, path))
                    try: os.remove(path)
                    except FileNotFoundError: pass
            except FileNotFoundError: pass
            except Exception as e:
                logger.error(f"[{self.phone_number}] Task loop error: {str(e)}")
                raise e
            await asyncio.sleep(1)

    async def add_task(self, task, taskFile:str):
        if type(task) == str: print(task)
        taskID = task.get("taskID",None)
        try:
            methods={
                "join_channel":joinChannel,
                "changeNotifyChannel":mute_unmute,
                "reportChannel":reportChat,
                "leave_channel":leaveChannel,
                "joinVoiceChat":joinVc,
                "leaveVoiceChat":leaveVc,
                "reactPost":reactPost,
                "sendMessage":sendMessage,
                "sendPhoto":sendPhoto,
                "votePoll":votePoll,
                "viewPosts":viewPost,
                "changeName":changeProfileName,
            }
            
            client = self.client
            phone_number = self.phone_number
            
            if not client.is_connected: await client.connect()
            
            try: await client.send_message("me","ping!")
            except: pass
            
            method = methods[task.get("type")]
            await method(
                phone_number=phone_number,
                task=task,
                client=client,
                self=self,
                taskID=taskID,
            )
        except (ChannelInvalid,ChannelPrivate,PeerIdInvalid,UserNotParticipant) as e:
            inviteLink=task.get("inviteLink",None)
            if not inviteLink: return
            # logger.info(f"<b>{phone_number}</b>: {task.get("chatID",None)}\nError: {e}\nJoining and Trying Again....")
            joinResult=await joinIfNot(client,task.get("chatID"),inviteLink)
            if not joinResult:
                # logger.critical(f"Failed To Join [{inviteLink}]: {joinResult}")
                try: os.remove(taskFile)
                except: pass
        except (UserAlreadyParticipant,MessageIdInvalid,InviteRequestSent): pass
        except FloodWait as e:
            # logger.error(f"[{phone_number}]: Flood wait [{e.value}s]")
            await asyncio.sleep(e.value)
            await self.add_task(task, taskFile)
        except Flood as err:
            if "FROZEN_METHOD_INVALID" in str(err):
                logger.error(f"<b>Account Frozen: {phone_number}</b>. <b>Account Removed</b>")
                Accounts.delete_one({"phone_number":str(phone_number)})
        except BotMethodInvalid:
            logger.error(f"Telegram Considering <b>{phone_number}</b> as Bot. <b>Account Removed</b>")
            Accounts.delete_one({"phone_number":str(phone_number)})
        except (ConnectionError,ConnectionAbortedError,OSError) as e:
            logger.critical(f"[{phone_number}] Fatal Connection Error: {e} — Restarting Client.")
            await self.restart_self()
        except (AuthKeyUnregistered,SessionRevoked,AuthKeyDuplicated) as e:
            await logChannel(f"Account Removed: {phone_number} Please login again: {str(e)}")
            Accounts.delete_one({"phone_number":str(phone_number)})
            await self.stop()
        except (UserDeactivated,UserDeactivatedBan):
            await logChannel(f"Account [{phone_number}]: Banned")
            Accounts.delete_one({"phone_number":str(phone_number)})
            await self.stop()
        except UsernameNotOccupied: 
            logger.warning(f"{phone_number}: <b>[USERNAME_NOT_OCCUPIED]</b>\n<pre>{format_json(task)}</pre>")
        except (InviteHashExpired): pass
        except (SessionPasswordNeeded): 
            password = self.accountData.get("password",None)
            if not password: return await logChannel(f"Session Password Needed for {phone_number}. Please set the password in the account data.")
            try: await client.check_password(password)
            except Exception as e:
                logger.error(f"Failed to check password for {phone_number}: {e}")
                return await logChannel(f"Failed to check password for {phone_number}: {e}")
            await self.add_task(task, taskFile)
        except Exception as e:
            if "closed database" in str(e):
                logger.error(f"Closed Database Error: {phone_number}. Restarting...")
                if not client.is_connected:
                    await client.connect()
            if task.get("session_string"): del task["session_string"]
            await logChannel(
                f"Error processing task for {phone_number}: <b>{str(e)}</b>\nType: {str(type(e))}\n\nTask Details:\n{format_json(task)}",
            )
            raise e

async def load_worker(worker_id):
    worker_path = os.path.join("workers", worker_id)
    accounts_file = os.path.join(worker_path, "accounts.json")
    queue_path = os.path.join(worker_path, "queue")
    os.makedirs(queue_path, exist_ok=True)

    global workers

    if os.path.exists(accounts_file):
        with open(accounts_file) as f:
            accounts = json.load(f)
        for phone in accounts:
            acc_file = os.path.join(ACCOUNT_FOLDER, phone, "account.json")
            if os.path.exists(acc_file):
                with open(acc_file) as af:
                    acc_data = json.load(af)
                worker = Worker(phone, acc_data)
                await worker.start()
                workers[phone] = worker

    async def watch_queue():
        while True:
            try:
                for fname in os.listdir(queue_path):
                    if worker_id == "worker_0": os.listdir(queue_path)
                    if not fname.endswith(".json"): continue
                    full_path = os.path.join(queue_path, fname)
                    with open(full_path) as f:
                        data = json.load(f)
                    phone = data.get("phone_number")

                    acc_file = os.path.join(ACCOUNT_FOLDER, phone, "account.json")
                    if os.path.exists(acc_file):
                        with open(acc_file) as af:
                            acc_data = json.load(af)
                        if phone not in workers:
                            # print(f"[{phone}]: Starting.......")
                            worker = Worker(phone, acc_data)
                            await worker.start()
                            workers[phone] = worker
                    os.remove(full_path)
            except Exception as e:
                logger.error(f"[Worker:{worker_id}] Queue watch error: {e}")
            await asyncio.sleep(2)

    
    safe_create_task(watch_queue())
    await asyncio.Event().wait()

async def cleanup(client: Client,phoneNumber):
    async for dialog in client.get_dialogs():
            chatID = dialog.chat.id
            if not Channels.find_one({"channelID":int(chatID)}):
                try:
                    await client.leave_chat(chatID)
                    if str(chatID).startswith("-100"): logger.info(f"[{phoneNumber}]: Left chat {dialog.chat.title} ({chatID})")
                except Exception as e: 
                    logger.error(f"Failed to leave chat {chatID}: {e}")
                    continue
    logger.warning(f"Cleanup completed for {phoneNumber}.")
    

if __name__ == "__main__":
    try:
        if len(sys.argv) < 2:
            logger.error("Usage: python3 worker.py <worker_id>")
            sys.exit(1)
        worker_id = sys.argv[1]
        asyncio.run(load_worker(worker_id))
    except KeyboardInterrupt as error:
        logger.warning(f"[{worker_id}]: process exited {error}")
    except Exception as error:
        logger.critical(f"[{worker_id}]: Process Exited {error}")

