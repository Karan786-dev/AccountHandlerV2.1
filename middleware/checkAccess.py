from config import ADMINS
from database import Admin
from pyrogram.types import InlineKeyboardButton , InlineKeyboardMarkup

async def checkAccess(_,message):
    if message.from_user.id in ADMINS:return True
    accessUsers = Admin.find_one({"accessUser":True}) or {}
    if message.from_user.id in accessUsers.get("list",[]): return True
    text = (
        "<b>🤦🏻‍♂ You Don't Have Access To The Bot!</b>\n\n"
        f"<b>Your UID: </b><code>{message.from_user.id}</code>"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Request Admin Access","/requestAdminAccess")]
    ])
    if getattr(message, "data", None): await message.message.reply(text,reply_markup=keyboard)
    else: await message.reply(text,reply_markup=keyboard)
    return False