from pyrogram import Client , filters
from pyrogram.types import Message
from database import *
import csv 
import  os

@Client.on_message(filters.command('channelsExpiry'))
async def knowAboutChannelsExpiry(client: Client,message: Message):
    cursor = Channels.find({"validity":True}, {"_id": 0, "title": 1, "daysLeft": 1,"inviteLink": 1})
    os.path.exists('temp') or os.makedirs('temp')
    filePath = 'temp/'+f"{message.id}-output.csv"
    with open(filePath, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["S.No", "Title", "Days Left", "Link"])
        for i, doc in enumerate(cursor, start=1): 
            title = doc.get("title", "")
            days_left = doc.get("daysLeft", 0)
            inviteLink = doc.get("inviteLink", "")
            status = "Expired!" if not days_left else days_left
            writer.writerow([i, title, status, inviteLink])
    await message.reply_document(filePath)
    os.remove(filePath)