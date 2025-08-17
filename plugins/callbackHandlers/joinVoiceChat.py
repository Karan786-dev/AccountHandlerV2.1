from pyrogram import Client, filters
from pyrogram.types import CallbackQuery
from config import * 
from ..responses.responseFunctions import createResponse

@Client.on_callback_query(filters.regex(r'^/joinVoiceChat'))
async def joinVoiceChat(client, query: CallbackQuery):
    await query.message.edit("🔒 Please provide channel username or if channel is private then send Invite Link",reply_markup=cancelKeyboard)
    createResponse(query.from_user.id,"joinVoiceChat")