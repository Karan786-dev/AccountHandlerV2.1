from pyrogram import Client, filters
from pyrogram.types import Message
from functions import *

@Client.on_message(filters.command("ping"))
async def ping(client: Client, message: Message):
    cpu_usage , memory_usage , disk_usage = get_vps_usage()
    start_t = datetime.now()
    await message.reply("Pong!")
    end_t = datetime.now()
    time_taken_s = (end_t - start_t).microseconds / 1000
    await message.reply(
        (
            f"**- Pyrogram:** `{time_taken_s} ms`\n"
            f"- **CPU Usage:** `{cpu_usage}%`\n"
            f"- **Ram Usage:** `{memory_usage}%`\n"
            f"- **Disk Usage:** `{disk_usage}%`")
        )