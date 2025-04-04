from pyrogram import Client, filters
from pyrogram.types import CallbackQuery
from config import * 
from ..responses.responseFunctions import * 

@Client.on_callback_query(filters.regex(r'/reportChat'))
async def reportChat(client: Client, query: CallbackQuery):
    await query.message.delete()
    await query.message.reply("<b>📨 Please provide invite link or username to proceed with sending spam report. 📬</b>",reply_markup=cancelKeyboard)
    createResponse(query.message.chat.id,"getChatIDToReport")