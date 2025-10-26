from pyrogram import Client , filters
from pyrogram.types import Message
from config import *
from functions import *
from logger import logger
from database import Accounts
import shutil


@Client.on_message(filters.command("createBackup"))
async def create_backup(client: Client, message: Message):
    if not message.from_user.id in ADMINS: return  
    try:
        await message.reply_text("<b>🔄 Creating backup, please wait...</b>")
        backupFolder = "sessions/backup"
        os.makedirs(backupFolder, exist_ok=True)

        for i in list(Accounts.find({})):
            phoneNumber = i.get("phone_number")
            sessionString = i.get("session_string")
            password = i.get("password")
            if os.path.exists("sessions/realBackup" + f"/{phoneNumber}.session"): continue
            hmsg = await message.reply_text(f"<b>📦 Creating backup for {phoneNumber}...</b>")
            try:
                sessionFile = await intercept_code_and_login(phoneNumber, sessionString, password, backupFolder)
                await hmsg.delete()
                await message.reply_document(
                    document=sessionFile,
                    caption=f"<b>✅ Backup created for {phoneNumber} successfully!</b>"
                )
                originalBackupFolder = "sessions/realBackup"
                os.makedirs(originalBackupFolder,exist_ok=True)
                dst = f"{originalBackupFolder}/{phoneNumber}.session"
                os.replace(sessionFile, dst)
            except Exception as e:
                logger.error(f"<b>❌ Error creating backup for {phoneNumber}: {e}</b>")
                try: await hmsg.edit_text(f"<b>❌ Error creating backup for {phoneNumber}: {e}</b>")
                except: await message.reply_text(f"<b>❌ Error creating backup for {phoneNumber}: {e}</b>",reply_to_message_id=message.id)
    except Exception as e:
        await message.reply_text(f"<b>❌ Error: {e}</b>")
        raise e