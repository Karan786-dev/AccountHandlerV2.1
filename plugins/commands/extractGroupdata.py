from pyrogram import Client , filters
from pyrogram.types import Message 
from pyrogram.errors import *
from ..responses.responseFunctions import * 
from database import *
from orderAccounts import UserbotManager
from functions import *


@Client.on_message(filters.command(r'extract'))
async def extractGroupData(client: Client, message: Message):
    link = message.text.split(" ")[1]
    if not link or (not link.startswith("https://") and not link.startswith("http://")):
        await message.reply_text("Please provide a valid group link.")
        return
    
    helperBot: Client = await UserbotManager.getSyncBotClient()
    try: 
        chatData = await helperBot.join_chat(link)
    except FloodWait as x: return await message.reply_text(f"<b>Please try again after {x.value} seconds</b>")
    except UserAlreadyParticipant: 
        chatData = await helperBot.get_chat(link)
    except Exception as error: return await message.reply_text(f"<b>Error while joining group</b>\n\n<code>{str(error)}</code>")

    wMSG = await message.reply_text("<b>Extracting members data......</b>")
    membersCount = await helperBot.get_chat_members_count(chatData.id)
    pictures = []
    names = []
    accountsData = shuffleArray(list(Accounts.find()))
    async for member in helperBot.get_chat_members(chatData.id,limit=len(accountsData)):
        user = member.user 
        userID = user.id  
        firstName = user.first_name 
        lastName = user.last_name or ""
        fullName = firstName + lastName
        photoID = user.photo.big_file_id if user.photo else False
        if photoID:
            photosPath = f"photos/{userID}.jpg"
            await helperBot.download_media(photoID,photosPath)
            pictures.append(photosPath)
        names.append(fullName)

    await wMSG.edit_text("<b>Members Data extracted. Now Changing accounts profiles</b>")
    await wMSG.edit_text(f"<b>Changing {len(accountsData)} Accounts...</b>")
    for i in range(len(names)):
        accountData = accountsData[i]
        phone = accountData.get("phone_number")
        if len(pictures) >= (i+1): await UserbotManager.add_task(phone,{
            "type": "changeProfilePicture",
            "photo": pictures[i],
        })
        await UserbotManager.add_task(phone,{
            "type": "changeName",
            "firstName": names[i].split(" ")[0],
            "lastName": names[i].split(" ")[1] if len(names[i].split(" ")) > 1 else ""
        })

    await wMSG.edit_text(f"<b>Succesfully Edited {len(accountsData)} Accounts</b>")