from pyrogram import Client , filters , types
from pyrogram.types import Message 
from database import Channels , Accounts
from orderAccounts import UserbotManager

async def messageHandler(_,message:Message):
    channelID = message.chat.id 
    channelData = Channels.find_one({"channelID":int(channelID)})
    if not channelData: return 
    chatUsername = message.chat.username
    inviteLink = f"@{chatUsername}" if chatUsername else channelData.get("inviteLink")
    messageID = message.id 
    postLink = f"https://t.me/c/{str(channelID).replace("-100","") if not chatUsername else chatUsername}/{messageID}"
    tasksData = channelData.get("services",[])
    if not len(tasksData):  return
    reactionEmojis = channelData.get('reactionsType', [])
    if ("view_posts" in tasksData) and channelData.get("isViewEnabled",False):
        viewRestTime = channelData.get("viewRestTime",0)
        viewCount = channelData.get("viewCount",0)
        userbots = list(Accounts.find({}))
        await UserbotManager.bulk_order(userbots,{
            "type":"viewPosts",
            "postLink": postLink,
            "restTime":float(viewRestTime),
            "taskPerformCount": int(viewCount),
            "inviteLink": inviteLink
        })
    if ("reaction_posts" in tasksData) and channelData.get("isReactionsEnabled",False) and len(reactionEmojis):
        reactRestTime = channelData.get('reactionRestTime',0)
        reactionCount = channelData.get('reactionsCount',0) 
        userbots = list(Accounts.find({}))
        await UserbotManager.bulk_order(userbots,{
            "type":"reactPost",
            "postLink": postLink,
            "restTime":float(reactRestTime),
            "taskPerformCount": int(reactionCount),
            "emoji":reactionEmojis,
            "inviteLink": inviteLink
        })
        
    
        
