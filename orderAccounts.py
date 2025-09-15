from pyrogram import Client
from config import USERBOT_SESSION
import asyncio
from pytgcalls.exceptions import*
import random
from pyrogram.errors import*
from database import Accounts,Channels
from pyrogram.handlers import MessageHandler,RawUpdateHandler
from pyrogram.enums import ChatMemberStatus
from functions import*
import os
from logger import logger
from methods import*
import json
import aiofiles
from pyrogram import *
from config import *
from pathlib import Path
from database import * 
from logger import logger
import aiofiles
from functions import *
import os
import json
import math
import subprocess
import shutil


MAX_ACCOUNTS_PER_PROCESS = 100

Path(ACCOUNT_FOLDER).mkdir(exist_ok=True, parents=True)


class OrderUserbotManager:
    def __init__(self):
        self.clients={}
        self.client_locks={}
        self.task_queues={}
        self.syncBotHelper={}
        self.sessionStrings={}
        self.syncBotHandlersData={}
        self.tasksData={}
        self.processes = []
        self.workers = {}
    
               
    def start_worker_processes(self):
        os.makedirs("workers", exist_ok=True)
        allAccounts = Accounts.find({"$or": [{"syncBot": {"$ne": True}}, {"helperBot": {"$ne": True}}]})
        phone_numbers = [acc["phone_number"] for acc in allAccounts]
        for i, j, k in os.walk("./Accounts/"):
            for n in j:
                if not n in phone_numbers:
                    dir_path = os.path.join(i, n)
                    if os.path.isdir(dir_path):
                        shutil.rmtree(dir_path)  # remove the directory and all its contents
                    else:
                        os.remove(dir_path)  # remove the file
        for phone_number in phone_numbers:  asyncio.create_task(self.assign_account_to_worker(phone_number))
        logger.info("[Manager] All worker processes handled.")


    async def assign_account_to_worker(self, phone_number: str):
        os.makedirs(WORKERS_DIR, exist_ok=True)
        # Look for a worker with space
        for worker_id in os.listdir(WORKERS_DIR):
            folder = os.path.join(WORKERS_DIR, worker_id)
            acc_file = os.path.join(folder, "accounts.json")
            if not os.path.exists(acc_file):
                continue
            with open(acc_file, "r") as f: accounts = json.load(f)
            if phone_number in accounts:
                return  # Already assigned
            if len(accounts) < MAX_ACCOUNTS_PER_PROCESS:
                accounts.append(phone_number)
                self._queue_account(phone_number, folder)
                if worker_id not in self.workers:
                    self.workers[worker_id] = []
                self.workers[worker_id].append(phone_number)
                with open(acc_file, "w") as f:
                    json.dump(accounts, f)
                return

        # All full → spawn new worker
        new_worker_id = f"worker_{len(os.listdir(WORKERS_DIR))}"
        new_folder = os.path.join(WORKERS_DIR, new_worker_id)
        os.makedirs(os.path.join(new_folder, "queue"), exist_ok=True)
        with open(os.path.join(new_folder, "accounts.json"), "w") as f:
            json.dump([phone_number], f)
        self._queue_account(phone_number, new_folder)
        self.workers[new_worker_id] = [phone_number]
        asyncio.create_task(self.create_new_process(new_worker_id))
        
    def stop_account(self, phone_number):
        targetWorkerID = None

        for workerID in self.workers:
            if phone_number in self.workers[workerID]: 
                targetWorkerID = workerID
                break

        if not targetWorkerID:
            print(f"[!] {phone_number} not assigned to any worker.")
            return False

        file_path = os.path.join(WORKERS_DIR, targetWorkerID, "accounts.json")

        try:
            with open(file_path, "r") as f:
                accounts = json.load(f)

            if phone_number in accounts:
                accounts.remove(phone_number)
                with open(file_path, "w") as f:
                    json.dump(accounts, f, indent=4)
                print(f"[✓] Removed {phone_number} from {file_path}")

                # Also remove from in-memory dict
                self.workers[targetWorkerID].remove(phone_number)

                return True
            else:
                print(f"[!] {phone_number} not found in {file_path}")
                return False
        except Exception as e:
            print(f"[!] Error modifying {file_path}: {e}")
            return False

            
    async def create_new_process(self,new_worker_id): subprocess.Popen(["python3", "worker.py", new_worker_id])
        
    def _queue_account(self, phone_number, worker_folder):
        accountData = Accounts.find_one({"phone_number": phone_number})
        if not accountData:
            logger.error(f"Account with phone number {phone_number} not found.")
            return
        for field in ["_id", "added_at"]:
            accountData.pop(field, None)
        os.makedirs(f"{ACCOUNT_FOLDER}/{phone_number}", exist_ok=True)
        with open(f"{ACCOUNT_FOLDER}/{phone_number}/account.json", "w") as f:
            json.dump(accountData, f, indent=4)

        queue_folder = os.path.join(worker_folder, "queue")
        with open(os.path.join(queue_folder, f"{phone_number}.json"), "w") as f:
            json.dump({"phone_number": phone_number}, f)


    async def bulk_order(self, userbots, task, isOldPending=False):
        # print(task)
        taskLimit=0
        tasksGathering=[]
        taskPerformCount=random.choice(task["taskPerformCount"]) if isinstance(task["taskPerformCount"],list) else task["taskPerformCount"]
        taskID=generateRandomString(10)
        task["taskID"]=taskID
        self.tasksData[taskID]=task
        taskID_2=task.get("taskID_2",None) if isOldPending else await self.saveTaskData(task,userbots)
        for userbot in userbots:
            if userbot.get("syncBot") or userbot.get("helperBot"): continue
            if not (taskID in self.tasksData):
                logger.error(f"<b>Task Deleted: </b><code>{taskID}</code>")
                break
            taskLimit+=1
            rest_time=task.get("restTime",0)
            if isinstance(rest_time,list) and len(rest_time)>1:
                rest_time=random.randint(int(rest_time[0]),int(rest_time[1]))
            elif isinstance(rest_time,list) and len(rest_time)==1:
                rest_time=rest_time[0]
            if rest_time!=0:
                self.tasksData[taskID]["canStop"]=True
                try: await asyncio.sleep(float(rest_time))
                except asyncio.CancelledError: pass
                await self.add_task(
                    phone_number=userbot["phone_number"],
                    task={
                        **task,
                        "session_string":userbot["session_string"],
                        "taskID_2":taskID_2
                    },
                )
            elif rest_time==0:
                self.tasksData[taskID]["canStop"]=False
                tasksGathering.append(self.add_task(
                    phone_number=userbot["phone_number"],
                    task={
                        **task,
                        "session_string":userbot["session_string"],
                    }))
            if taskLimit>=int(taskPerformCount):
                break
        await asyncio.gather(*tasksGathering)
        await self.deleteTasksJsonData(taskID_2)
        
    async def add_task(self, phone_number, task):
        try: 
            accountData = Accounts.find_one({"phone_number":phone_number})
            os.makedirs(f"{ACCOUNT_FOLDER}/{phone_number}/tasksData/",exist_ok=True)
            taskID = task.get("taskID", generateRandomString())
            
            with open(f"{ACCOUNT_FOLDER}/{phone_number}/tasksData/{taskID}.json", "w") as f:
                f.write(json.dumps(task, indent=4))
                f.close()
            taskID_2=task.get("taskID_2",None)
            await self.removeUserbotFromTaskData(taskID_2,phone_number)
            
        except Exception as e: raise e
       

    async def watch_posts_folder(self):
        POSTS_FOLDER = "syncbot/posts"
        os.makedirs(POSTS_FOLDER, exist_ok=True)
        logger.info("[SyncBot] Watching posts folder...")
        while True:
            try:
                files = os.listdir(POSTS_FOLDER)
                for filename in files:
                    if not filename.endswith(".json"): continue
                    filepath = os.path.join(POSTS_FOLDER, filename)
                    async with aiofiles.open(filepath, "r") as f:
                        content = await f.read()
                        if not content.strip(): continue
                    try:
                        post_data = json.loads(content)
                        userbots = post_data.get("userbots") or list(Accounts.find({"syncBot": {"$ne": True}}))
                        safe_create_task(self.bulk_order(userbots, post_data))
                        logger.info(f"[SyncBot] Processed post task: {filename}, {len(userbots)} userbots")
                    except Exception as e: logger.error(f"[SyncBot] Error processing {filename}: {e}")
                    
                    os.remove(filepath)

            except Exception as e:
                logger.critical(f"[SyncBot] Folder watch failed: {e}")
            await asyncio.sleep(1)

    async def getSyncBotClient(self,isNew=False):
        if ("client" in self.syncBotHelper) and not isNew: return self.syncBotHelper["client"]

        helperBotData = Accounts.find_one({"helperBot": True})
        if not helperBotData: raise Exception("Helper sync bot not found in database.")

        session_string = helperBotData.get("session_string")
        phone_number = helperBotData.get("phone_number")

        if not session_string: raise Exception(f"Session string not found for helper bot ({phone_number})")

        client = Client(
            name=phone_number,
            api_id=API_ID,
            api_hash=API_HASH,
            session_string=session_string
        )
        self.syncBotHelper["client"] = client
        await client.connect()
        return client
        
    async def saveTaskData(self, task, userbots):
        try:
            taskType = task["type"]
            taskID_2 = generateRandomString(10)
            task["taskID_2"] = taskID_2
            if taskType == "joinVoiceChat": return taskID_2
            data = {
                "task": task,
                "userbots": {ub["phone_number"]: {k:v for k,v in ub.items() if k not in ["_id","added_at"]} 
                            for ub in userbots}
            }
            
            os.makedirs("tasksData", exist_ok=True)
            async with aiofiles.open(f"tasksData/{taskID_2}.json", "w") as f:
                json_str = json.dumps(data)
                await f.write(json_str)
                await f.flush()
            return taskID_2
        except Exception as e:
            logger.error(f"Error saving task data: {str(e)}")
            raise

    async def removeUserbotFromTaskData(self, taskID_2, phone_number):
        try:
            async with aiofiles.open(f"tasksData/{taskID_2}.json", "r") as f:
                content = await f.read()
                if not content.strip(): 
                    await self.deleteTasksJsonData(taskID_2)
                    return
                data = json.loads(content)
            userbotsJson = data.get("userbots", {})
            if phone_number in userbotsJson: 
                del userbotsJson[phone_number]
            async with aiofiles.open(f"tasksData/{taskID_2}.json", "w") as f:
                await f.write(json.dumps({"task": data.get("task", {}), "userbots": userbotsJson}))
        except json.JSONDecodeError:
            await self.deleteTasksJsonData(taskID_2)
        except FileNotFoundError:
            pass
        except Exception as e:
            logger.critical(f"Error While Removing Userbot From Task Data: {phone_number} - {str(e)}")
            
    async def deleteTasksJsonData(self,taskID_2):
        file=f"tasksData/{taskID_2.replace('.json','')}.json"
        if os.path.exists(file): os.remove(file)

    async def restartPendingTasks(self):
        tasksData = os.listdir("tasksData")
        for filename in tasksData:
            try:
                filepath = f"tasksData/{filename}"
                async with aiofiles.open(filepath, "r") as f:
                    content = await f.read()
                    
                if not content.strip():
                    await self.deleteTasksJsonData(filename)
                    continue
                    
                data = json.loads(content)
                if not data.get("userbots"):
                    await self.deleteTasksJsonData(filename)
                    continue
                    
                userbotsArray = list(data["userbots"].values())
                asyncio.create_task(self.bulk_order(userbotsArray, data["task"], isOldPending=True))
                
            except (json.JSONDecodeError, KeyError):
                await self.deleteTasksJsonData(filename)
                logger.warning(f"Removed corrupted task file: {filename}")
            except Exception as error:
                logger.critical(f"Error Restarting Task [{filename}]: {error}")

UserbotManager=OrderUserbotManager()    