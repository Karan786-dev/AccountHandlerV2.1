import asyncio
import sys
from config import *
import monkeyPatches
from pyrogram import Client, idle 
from functions import *
from pathlib import Path
from orderAccounts import UserbotManager
from database import Accounts
from asyncio.exceptions import *
from logger import logger
from booster import boosterBot
from pyrogram.errors import *
from dailyActivity import *
import os
import shutil
import resource

soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
if soft < hard:
    resource.setrlimit(resource.RLIMIT_NOFILE, (hard, hard))


    
Path(SESSION).mkdir(exist_ok=True,parents=True)
Path(USERBOT_SESSION).mkdir(exist_ok=True,parents=True)

try: shutil.rmtree(WORKERS_DIR)
except Exception as e: pass

if not os.path.exists("tasksData"): os.mkdir("tasksData")

proxyDetail=f"v2.proxyempire.io:5000:r_3ce61fadce-sid-AccountHandlerBot-V3:5f44dcfd3f"
ip,port,username,password=proxyDetail.split(":")
proxy={
        "hostname":ip,
        "port":int(port),
        "username":username,
        "password":password,
        "scheme":"socks5"
}

class Bot(Client):
    def __init__(self):
        super().__init__(
            name=SESSION+"/mainBot",
            api_id=API_ID,
            api_hash=API_HASH,
                bot_token=BOT_TOKEN,
                workers=50,
            plugins={"root": "plugins"},
        )

    async def start(self,*args, **kwargs):
        try:
            await super().start()
            me = await self.get_me()
            temp.ME = me.id
            temp.U_NAME = me.username
            temp.B_NAME = me.first_name
            self.username = '@' + me.username
            await logChannel(f"<b>✅ Bot Successfully Started!</b>\n<b>🤖 Bot Username:</b> @{me.username}")
            if restart_pending_tasks: asyncio.create_task(UserbotManager.restartPendingTasks())
            # if restart_pending_activity_tasks: asyncio.create_task(restart_pendingLeaves())
            # asyncio.create_task(startRandomActivityInChannels())
            asyncio.create_task(self.startBooster())
            syncBotData = Accounts.find_one({"syncBot":True})
            
            if not syncBotData: return await logChannel("<b>🚫 Syncer Bot not Available.</b>")
            safe_create_task(UserbotManager.watch_posts_folder())
            UserbotManager.start_worker_processes()
            # asyncio.create_task(bulkJoinChannels())
            # asyncio.create_task(changeAllAccountsName())
            # asyncio.create_task(refreshReactions())
        except FloodWait as x:
            await logChannel(f"<b>🚫 FloodWait: {x.value}s on starting Main Bot</b>",)
            sys.exit()
        except Exception as e:
            print(f"Error starting bot: {e}")
            raise e
    async def startBooster(self):
        try:
            await boosterBot.start()
            await logChannel(f"<b>✅ Booster Bot Successfully Started: @{(await boosterBot.get_me()).username}</b>")
        except FloodWait as x:
            await logChannel(f"<b>🚫 FloodWait: {x.value}s on starting Booster Bot\nRestarting after {x.value}s</b>",)
            await asyncio.sleep(x.value+1)
            await self.startBooster()
            # sys.exit()
        except Exception as e:
            print(f"Error starting booster bot: {e}")
            raise e
    async def stop(self, *args):
        try:
            workersProcess = UserbotManager.processes
            if len(workersProcess):
                logger.warning(f">> Terminating {len(workersProcess)} Workers")
                for process in workersProcess:
                    process.terminate()
                logger.warning(">> Done terminating workers")
            pendingTask = asyncio.all_tasks()
            if len(pendingTask):
                logger.warning(f">> Cancelling tasks now: {len(pendingTask)} Tasks")
                for task in pendingTask:
                    task.cancel()
                logger.warning(">> Done cancelling tasks")
            logger.warning('>> Shutting down main bot')
            await super().stop()
        except CancelledError: pass
        sys.exit()

async def refreshReactions():
    channelsLinks = [
        "https://t.me/+E0tzx0JpQv40ZTQ9",
        "https://t.me/+-wY6N1auuOszOTU1",
        "https://t.me/+PsAlNqtivAliZWU1",
        "https://t.me/+0tBhz1lB22AwZjI1",
        # "https://t.me/+j4ZREH4O0jdkYTZl",
        "https://t.me/+kMVeGa1IzUM5MjY1",
        "https://t.me/+jhi01Z-3MMg1YWFh"
    ]
    helperBot: Client = await UserbotManager.getSyncBotClient()
    for link in channelsLinks:
        chatInfo = None
        chatID = None
        chatInfo = await helperBot.get_chat(link)
        
        if not chatInfo: 
            logger.warning(f"[{link}]: Id not found.")
            continue
        channelID = chatInfo.id
        # if not Channels.find_one({"channelID":channelID}):
        logger.debug(f"Channel {chatInfo.title}: {chatInfo.available_reactions}")
        Channels.update_one({
                "channelID": channelID,
            },{"$set":{"title": chatInfo.title,
                "inviteLink": link,
                "isBoosterEnabled": True,
                "isViewEnabled": True,
                "isReactionsEnabled": True,
                "viewCount": 0,
                "reactionsCount": 200,
                "reactionsType": [i.emoji for i in chatInfo.available_reactions.reactions],
                }},upsert=True)
        logger.debug(f"Channel {chatInfo.title} Reactions updated")
        
async def bulkJoinChannels():

    channelsLink =  [
    "https://t.me/+E0tzx0JpQv40ZTQ9",
    "https://t.me/+-wY6N1auuOszOTU1",
    "https://t.me/+PsAlNqtivAliZWU1",
    "https://t.me/+0tBhz1lB22AwZjI1",
    "https://t.me/+j4ZREH4O0jdkYTZl",
    "https://t.me/+kMVeGa1IzUM5MjY1",
    "https://t.me/+ww_fLnUFomc2MTQ1",
    "https://t.me/+CI1d9S5oLyEzZDk1"
]
    helperBot: Client = await UserbotManager.getSyncBotClient()
    for link in channelsLink:
        chatInfo = None
        chatID = None
        if Channels.find_one({"inviteLink":link}): continue
        try: chatInfo = await helperBot.join_chat(link)
        except FloodWait as e:
            logger.error(f"<b>🚫 FloodWait: {e.value}s on joining channel {link}</b>")
            await asyncio.sleep(e.value + 1)
            try: chatInfo = await helperBot.join_chat(link)
            except UserAlreadyParticipant:
                chatInfo = await helperBot.get_chat(link)
            except Exception as err: 
                raise err
        except (InviteRequestSent): pass
        except UserAlreadyParticipant:
            chatInfo = await helperBot.get_chat(link)
        except Exception as e:
            print(f"Error joining channel {link}: {e}")
            continue
        
        if not chatInfo: 
            logger.warning(f"[{link}]: Id not found.")
            continue
        channelID = chatInfo.id
        if not hasattr(chatInfo.available_reactions,"reactions"): 
            logger.warning(f"Channel {chatInfo.title} does not have reactions enabled. Skipping...")
            continue
        # if not Channels.find_one({"channelID":channelID}):
        Channels.update_one({
                "channelID": channelID,
            },{"$set":{"title": chatInfo.title,
                "inviteLink": link,
                "isBoosterEnabled": True,
                "isViewEnabled": True,
                "isReactionsEnabled": True,
                "viewCount": 0,
                "reactionsCount": 200,
                "reactionsType": [i.emoji for i in chatInfo.available_reactions.reactions],
                "services": ["view_posts", "reaction_posts"],
                "validity": True,
                "daysLeft": 26}},upsert=True)
        logger.debug(f"Joined and added channel: {chatInfo.title} ({link})")

async def changeAllAccountsName():
    accounts = list(Accounts.find({}))
    for i in accounts:
        newName = getRandomName()
        while Accounts.find_one({"name":newName}): newName = getRandomName()
        await UserbotManager.add_task(
            i.get('phone_number'),
            {
                "type": "changeName",
                "firstName": newName.split(" ")[0],
                "lastName": newName.split(" ")[1]
            }
        )
        Accounts.update_one({"phone_number":i.get("phone_number")},{"$set":{"name":newName}})




try:
    app = Bot()
    app.run()
    idle()
    app.stop()
except KeyboardInterrupt: logger.warning("Ctrl+C Pressed. Shutting Down.....")
