from pyrogram import Client , filters , idle
from pyrogram.types import *
from functions import get_vps_usage
import asyncio
from config import *
import os
client = Client(
            name="sessions/mypinger",
            api_id=3269267,
            api_hash="d23d55a7cf2c18966a1b252250754a58",
            phone_number="919878123956"
        )

@client.on_message(filters.command("restart_krdo_bhai"))
async def restartCommand(bot: Client,message: Message):
    if message.from_user.id in ADMINS:
        os.system("pm2 restart all")
        await message.reply("<b>Ofc, You are the gayiest person i have ever meet.</b>")


async def pinger():
    
    print(f"Pinging started........")
    while True:
        cpu , mem , disk , up = get_vps_usage()

        text = f"""
<b>
Hello :)

VPS Usage Report:

CPU Usage: {cpu}%
Memory Usage: {mem}%
Disk Usage: {disk}%
</b>
"""
        
        if mem > 70:
            os.system("pm2 restart all")
            text = """
<b>
🔴 Memory limit crossed

⚙️ All pm2 processes restarting.
</b>
"""
        try:
            await client.send_message(
            chat_id=LOGGING_CHANNEL,
            text=text
            )
        except Exception as error: print(error)

        await asyncio.sleep(10*60)



