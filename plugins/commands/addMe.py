from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from config import *
from pyrogram.errors import *

@Client.on_message(filters.command("addme") & filters.private)
async def addMe(client: Client,message: Message):
    await message.reply_text(
        "Send me your contact.",
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("Share Contact", request_contact=True)]],
        )
    )

@Client.on_message(filters.contact & filters.private)
async def handle_contact(client: Client, message: Message):
    contact = message.contact
    if contact:
        phoneNumber = contact.phone_number
        userbotClient = Client(USERBOT_SESSION + "/" + phoneNumber, api_id=API_ID, api_hash=API_HASH)
        try: 
            await userbotClient.connect()
        
        except Exception as e:
            await message.reply_text(f"Failed to connect: {str(e)}")
            return
        send_code = await userbotClient.send_code(phone_number=phoneNumber)
        await message.reply("<b>✅ Code Sent Successfully, Enter Your Code</b>")
        otpMsg = await client.listen(message.chat.id)
        otpCode = otpMsg.text.strip()
        password = None
        try: await userbotClient.sign_in(phone_number=phoneNumber, phone_code=otpCode,phone_code_hash=send_code.phone_code_hash)
        except SessionPasswordNeeded: 
            password = await client.ask(message.chat.id, "Enter your 2FA password:")
            await userbotClient.check_password(password.text)
        except Exception as e:
            await message.reply_text(f"Failed to sign in: {str(e)}")
            return
        from database import Accounts
        from datetime import datetime
        sessionString = await userbotClient.export_session_string()
        await message.reply("<b>✅ Account Authenticated Successfully</b>",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Add Another","/add_account")]]))
        botInfoFromTg = await userbotClient.get_me()
        accountData = {
            "phone_number": phoneNumber,
            "added_at": datetime.now(),
            "session_string": sessionString,
            "password": password.text,
        }
        accountData["username"] = botInfoFromTg.username if botInfoFromTg.username else None
        Accounts.update_one({"phone_number": phoneNumber}, {"$set": accountData}, upsert=True)
        await userbotClient.disconnect()
        
    else:
        await message.reply_text("No contact information received.")