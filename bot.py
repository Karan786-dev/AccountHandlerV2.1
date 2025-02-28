import asyncio
import sys
from config import SESSION, API_HASH, API_ID, BOT_TOKEN, USERBOT_SESSION
from pyrogram import Client, idle  # type: ignore
from functions import temp , logChannel
from pathlib import Path
from orderAccounts import UserbotManager
from database import Accounts
import shutil
from asyncio.exceptions import *
from logger import logger


if Path(SESSION).exists(): shutil.rmtree(SESSION)
if Path(USERBOT_SESSION).exists(): shutil.rmtree(USERBOT_SESSION)
    
Path(SESSION).mkdir(exist_ok=True,parents=True)
Path(USERBOT_SESSION).mkdir(exist_ok=True,parents=True)


class Bot(Client):
    def __init__(self):
        super().__init__(
            name=SESSION+"/mainBot",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            workers=500,
            plugins={"root": "plugins"},
            sleep_threshold=5,
        )

    async def start(self,*args, **kwargs):
        try:
            await super().start()
            me = await self.get_me()
            temp.ME = me.id
            temp.U_NAME = me.username
            temp.B_NAME = me.first_name
            self.username = '@' + me.username
            logChannel(f"<b>✅ Bot Successfully Started!</b>\n<b>🤖 Bot Username:</b> @{me.username}")
            syncBotData = Accounts.find_one({"syncBot":True})
            if not syncBotData: return logChannel("<b>🚫 Syncer Bot not Available.</b>")
            await UserbotManager.start_client(syncBotData.get("session_string"),syncBotData.get("phone_number"),isSyncBot=True)
        except Exception as e:
            print(f"Error starting bot: {e}")
            raise e

    async def stop(self, *args):
        try:
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

try:
    app = Bot()
    app.run()
    idle()
    app.stop()
except KeyboardInterrupt: logger.warning("Ctrl+C Pressed. Shutting Down.....")
