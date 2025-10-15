from pyrogram import Client 
from database import * 
from logger import *

_original_join_chat = Client.join_chat
_original_leave_chat = Client.leave_chat

async def join_chat_hook(self, chat_id):
    result = await _original_join_chat(self, chat_id)
    phone = (await self.get_me()).phone_number
    logger.info(f"[{phone}]: Joined {result.title}")
    Chats.update_one({"phone_number": phone}, {"$addToSet": {"joined": result.id}}, upsert=True)
    return result

async def leave_chat_hook(self, chat_id,delete=True):
    phone = (await self.get_me()).phone_number
    result = await _original_leave_chat(self, chat_id,delete=delete)
    logger.info(f"[{phone}]: Leaved {chat_id}")
    Chats.update_one({"phone_number": phone}, {"$pull": {"joined": chat_id}}, upsert=True)
    return result

Client.join_chat = join_chat_hook
Client.leave_chat = leave_chat_hook