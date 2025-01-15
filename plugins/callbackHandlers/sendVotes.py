from pyrogram import * 
from pyrogram.types import *
from config import *
from ..responses.responseFunctions import *


@Client.on_callback_query(filters.regex(r"^/sendVotes"))
async def sendVotesHandler(_,query: CallbackQuery):
    await query.message.delete()
    await query.message.reply("<b>📨 Please provide the post link to proceed with sending votes. 📬</b>",reply_markup=cancelKeyboard)
    createResponse(query.message.chat.id,"postLinkToVote")