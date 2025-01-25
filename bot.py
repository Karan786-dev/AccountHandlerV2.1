import asyncio
import os
import sys
import subprocess
from config import SESSION, API_HASH, API_ID, BOT_TOKEN, USERBOT_SESSION
from pyrogram import Client, idle  # type: ignore
from functions import temp
from pathlib import Path
from orderAccounts import UserbotManager
from database import Accounts
import shutil

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
            print(f"Bot started!!!!!")
            print(
                f"""Bot Information:
Username: @{me.username}"""
            )
            syncBotData = Accounts.find_one({"syncBot":True})
            if not syncBotData: return print("Sync Bot Not Found")
            await UserbotManager.start_client(syncBotData.get("session_string"),syncBotData.get("phone_number"),isSyncBot=True)
            from test import main
            # await main()
        except Exception as e:
            print(f"Error starting bot: {e}")
            raise e

    async def stop(self, *args):
        print('Stopping main bot............')
        await super().stop()
        print("Stopping Active Userbots")
        await UserbotManager.stop_all_client()
        sys.exit()

app = Bot()
app.run()
idle()
app.stop()
