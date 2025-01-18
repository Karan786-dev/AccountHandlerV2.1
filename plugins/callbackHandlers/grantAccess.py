from pyrogram import Client , filters 
from config import ADMINS, cancelKeyboard
from markups import grantAccessMarkup , manageBotAccessMarkup
from database import Admin
from ..responses.responseFunctions import createResponse 


@Client.on_callback_query(filters.regex(r'^/manageAccess'))
async def manageAccess(_,query):
    text , keyboard = await manageBotAccessMarkup()
    await query.message.edit(text,reply_markup=keyboard)


@Client.on_callback_query(filters.regex(r'^/grantAccess'))
async def adminGrantAccess(_,query):
    await query.message.edit("<b>Send User ID to change Access to Bot.</b>",reply_markup=cancelKeyboard)
    createResponse(query.from_user.id,"askUserIDForAccess")

@Client.on_callback_query(filters.regex(r'^/requestAdminAccess'))
async def requestAdminAccessHandler(_,query):
    await query.message.edit("<b>✅ Your request has been sent for review.</b>")
    text,keyboard = await grantAccessMarkup(query.from_user.id)
    for i in ADMINS: await _.send_message(i,text,reply_markup=keyboard)
    
    
@Client.on_callback_query(filters.regex(r'^/changeAccess'))
async def changeAccessHandler(_,query):
    userID = query.data.split(maxsplit=1)[1]
    accessUsers = Admin.find_one({"accessUser":True}) or {}
    usersList = accessUsers.get("list",[])
    if int(userID) in usersList:
        Admin.update_one({"accessUser":True},{"$pull":{"list":int(userID)}},upsert=True)
    else:
        Admin.update_one({"accessUser":True},{"$push":{"list":int(userID)}},upsert=True)
    text , keyboard = await manageBotAccessMarkup()
    await query.message.edit(text,reply_markup=keyboard)
    