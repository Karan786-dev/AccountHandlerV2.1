from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup , Reaction
from database import Channels, Admin, Accounts , ActivityChannels
from orderAccounts import UserbotManager
from functions import convertTime, paginateArray
from pyrogram import Client
from logger import logger



async def manageBotAccessMarkup():
    accessUsers = Admin.find_one({"accessUser":True}) or {}
    usersList = accessUsers.get("list",[])
    keyboard = [
    [
        InlineKeyboardButton(f"🔹 {i}", "/nothingBruh"),
        InlineKeyboardButton(
            "✅ Grant Access" if (not int(i) in usersList) else "❎ Remove Access",
            f"/changeAccess {i}"
        )
    ] for i in usersList
    ]
    keyboard.append([
        InlineKeyboardButton("➕ Add Access", "/grantAccess")
    ])
    keyboard.append([
        InlineKeyboardButton("🔙 Back to Panel", "admin")
    ])
    text = "<b>🔐 Manage Bot Access</b>\n\nSelect a user to grant or revoke access."
    return text, InlineKeyboardMarkup(keyboard)




#For admin
async def grantAccessMarkup(userID):
    accessUsers = Admin.find_one({"accessUser":True}) or {}
    usersList = accessUsers.get("list",[])
    text = f"<b>UserID: </b><code>{userID}</code>"
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("✅ Grant Access" if (not int(userID) in usersList) else "❎ Remove Access",f"/changeAccess {userID}")]
        ]
    )
    return text, keyboard

# For Admin
def adminPanel(fromUser):
    text = (
        "<b>👋 Welcome, Admin!</b>\n\n"
        "🔹 Use the buttons below to manage the bot and its users."
    )
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔐 Manage Access", callback_data="/manageAccess"),
            InlineKeyboardButton("📢 Broadcast", callback_data="/broadcast")
        ],
        [
            InlineKeyboardButton("📋 Telegram Accounts", callback_data="/manageAccountAdmin"),
            InlineKeyboardButton("📡 Manage Channels", callback_data="/manageChannels")
        ],
        [
            InlineKeyboardButton("📊 Daily Activity","/DailyActivityChannels")
        ]
    ])
    return text, keyboard


def mainMenu(fromUser):
    text = (
        f"<b>👋 Hello, {fromUser.first_name}!</b>\n\n"
        "🔹 Use the buttons below to access different features."
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📩 Send Message", callback_data="/sendMessage")],
        [
            InlineKeyboardButton("🔔 Join Chat", callback_data="/joinChats"),
            InlineKeyboardButton("🔕 Leave Chat", callback_data="/leaveChats")
        ],
        [
            InlineKeyboardButton("👀 Boost Views", callback_data="/sendViews"),
            InlineKeyboardButton("❤️ Send Reactions", callback_data="/sendReactions")
        ],
        [
            InlineKeyboardButton("🗳 Cast Votes", callback_data="/sendVotes"),
            InlineKeyboardButton("🎙 Join Voice Chat", callback_data="/joinVoiceChat")
        ],
        [
            InlineKeyboardButton("🚨 Report Chat", callback_data="/reportChat"),
            InlineKeyboardButton("🔕 Mute/Unmute", callback_data="/notifyChangeChat")
        ],
        [InlineKeyboardButton("📸 Send Photo", callback_data="/sendPhoto")],
    ])

    return text, keyboard


async def manageChannelServices(channelID):
    channelData = Channels.find_one({"channelID": int(channelID)})
    text = (
        f"<b>📢 Channel Title:</b> <code>{channelData.get('title', 'N/A')}</code>\n\n"
        "📊 <b>Auto Views:</b>\n"
        f"   ├─ <b>Status:</b> {'✅ Enabled' if channelData.get('isViewEnabled', False) else '❎ Disabled'}\n"
        f"   ├─ <b>Delay:</b> {channelData.get('viewRestTime', 0)} sec\n"
        f"   └─ <b>Views per Post:</b> {channelData.get('viewCount', 0)}\n\n"
        "🎭 <b>Auto Reactions:</b>\n"
        f"   ├─ <b>Status:</b> {'✅ Enabled' if channelData.get('isReactionsEnabled', False) else '❎ Disabled'}\n"
        f"   ├─ <b>Delay:</b> {channelData.get('reactionRestTime', 0)} sec\n"
        f"   ├─ <b>Reactions per Post:</b> {channelData.get('reactionsCount', 0)}\n"
        f"   └─ <b>Emojis:</b> {' '.join(channelData.get('reactionsType', [])) or 'None'}\n\n"
        "🎙 <b>Auto Voice Join:</b>\n"
        f"   ├─ <b>Status:</b> {'✅ Enabled' if channelData.get('isVoiceEnabled', False) else '❎ Disabled'}\n"
        f"   ├─ <b>Delay:</b> {channelData.get('voiceRestTime', 0)} sec\n"
        f"   ├─ <b>Duration:</b> {channelData.get('voiceDuration', 0)} sec\n"
        f"   └─ <b>Join Count:</b> {channelData.get('voiceCount', 0)}\n\n"
        f"🚀 <b>Booster Status:</b> {'✅ Enabled' if channelData.get('isBoosterEnabled', False) else '❎ Disabled'}\n\n"
        "⚙️ Use the buttons below to modify settings."
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🚀 Disable Booster" if channelData.get("isBoosterEnabled") else "🚀 Enable Booster", callback_data=f"/toggle_booster {channelID}")
        ],
        [
            InlineKeyboardButton("📊 Auto Views", callback_data="nothing")
        ],
        [
            InlineKeyboardButton("⏳ Delay", callback_data=f"/changeDelay views {channelID}"),
            InlineKeyboardButton("📈 Per Post", callback_data=f"/changeCount views {channelID}"),
            InlineKeyboardButton("❎ Disable" if channelData.get("isViewEnabled") else "✅ Enable", callback_data=f"/toggle_views {channelID}"),
        ],
        [
            InlineKeyboardButton("🎭 Auto Reactions", callback_data="nothing")    
        ],
        [
            InlineKeyboardButton("⏳ Delay", callback_data=f"/changeDelay reactions {channelID}"),
            InlineKeyboardButton("📈 Per Post", callback_data=f"/changeCount reactions {channelID}"),
            InlineKeyboardButton("❎ Disable" if channelData.get("isReactionsEnabled") else "✅ Enable", callback_data=f"/toggle_reactions {channelID}"),
        ],
        [
            InlineKeyboardButton("😊 Reaction Emojis", callback_data=f"/reactionEmoji {channelID}"),
        ],
        [
            InlineKeyboardButton("Auto Poll Votes",f"/autoVotes {channelID}")
        ],
        [
            InlineKeyboardButton("🎙 Auto Voice Join", callback_data="nothing")
        ],
        [
            InlineKeyboardButton("⏳ Delay", callback_data=f"/changeDelay voice {channelID}"),
            InlineKeyboardButton("🔢 Join Count", callback_data=f"/changeCount voice {channelID}"),
            InlineKeyboardButton("❎ Disable" if channelData.get("isVoiceEnabled") else "✅ Enable", callback_data=f"/toggle_voice {channelID}"),
        ],
        [
            InlineKeyboardButton("⏱ Duration", callback_data=f"/changeVoiceDuration {channelID}"),    
        ],
        [
            InlineKeyboardButton("🔙 Back", callback_data=f"/viewChannel {channelID}"),
            InlineKeyboardButton("🏠 Main Menu", callback_data="admin"),
        ]
    ])

    return text, keyboard


#For Admin
async def manageChannelMarkup(page: int = 1, per_page: int = 10):
    allChannels = list(Channels.find({})) or []
    totalChannels = len(allChannels)
    
    backButton = InlineKeyboardButton("🔙 Back", callback_data="admin")
    addChannelButton = InlineKeyboardButton("➕ Add Channel", callback_data="/addChannel")

    if totalChannels == 0:
        text = "<b>🚫 No channels added yet.\nUse the button below to add new channels.</b>"
        keyboard = InlineKeyboardMarkup([[addChannelButton], [backButton]])
        return text, keyboard

    start = (page - 1) * per_page
    end = start + per_page
    channelsToDisplay = allChannels[start:end]
    total_pages = (totalChannels + per_page - 1) // per_page 

    text = f"<b>Manage Channels </b>(Page {page}/{total_pages}):\n\n<b>Select a Channel</b> from the list below:\n"
    
    keyboard_buttons = [
        [InlineKeyboardButton(f"{i}. {channelData.get('title') or channelData.get('channelID')}", 
                              callback_data=f"/viewChannel {channelData.get('channelID')}")]
        for i, channelData in enumerate(channelsToDisplay, start=start + 1)
    ]

    navigation_buttons = []
    if page > 1:
        navigation_buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"/manageChannels {page - 1}"))
    if page < total_pages:
        navigation_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"/manageChannels {page + 1}"))

    keyboard = InlineKeyboardMarkup(
        keyboard_buttons + 
        ([navigation_buttons] if navigation_buttons else []) + 
        [[addChannelButton, backButton]]
    )

    return text, keyboard

async def manageChannelActivityMarkup(page: int = 1, per_page: int = 5):
    allChannels = list(ActivityChannels.find({})) or []
    totalChannels = len(allChannels)
    
    backButton = InlineKeyboardButton("🔙 Back", callback_data="admin")
    addChannelButton = InlineKeyboardButton("➕ Add Channel", callback_data="/ChannelActivityAdd")

    if totalChannels == 0:
        text = "<b>🚫 No channels added yet.\nUse the button below to add new channels.</b>"
        keyboard = InlineKeyboardMarkup([[addChannelButton], [backButton]])
        return text, keyboard

    start = (page - 1) * per_page
    end = start + per_page
    channelsToDisplay = allChannels[start:end]
    total_pages = (totalChannels + per_page - 1) // per_page 

    text = f"<b>Manage Channels Daily Activities </b>(Page {page}/{total_pages}):\n<b>Select a Channel</b> from the list below:\n"
    
    keyboard_buttons = [
        [InlineKeyboardButton(f"{i}. {channelData.get('title') or channelData.get('channelID')}", 
                              callback_data=f"/ChannelActivityView {channelData.get('channelID')}")]
        for i, channelData in enumerate(channelsToDisplay, start=start + 1)
    ]

    navigation_buttons = []
    if page > 1:
        navigation_buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"/DailyActivityChannels {page - 1}"))
    if page < total_pages:
        navigation_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"/DailyActivityChannels {page + 1}"))

    keyboard = InlineKeyboardMarkup(
        keyboard_buttons + 
        ([navigation_buttons] if navigation_buttons else []) + 
        [[addChannelButton, backButton]]
    )

    return text, keyboard
      
async def viewChannelActivity(channelID: int, channelData=0):
    channelData = channelData or ActivityChannels.find_one({"channelID": channelID})
    if not channelData:
        return "❌ <b>Error: Channel not found!</b>", InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙 Back", callback_data="/DailyActivityChannels 1")]]
        )
    channelType = channelData.get('type', 'Unknown')
    channelLink = channelData.get('inviteLink', 'No invite link')
    channelUsername = channelData.get("username")
    channelTitle = channelData.get('title', 'Untitled Channel')
    maxJoinDelay = channelData.get("maxJoinDelay", 0)
    minJoinDelay = channelData.get("minJoinDelay", 0)
    maxLeaveDelay = channelData.get("maxLeaveDelay", 0)
    minLeaveDelay = channelData.get("minLeaveDelay", 0)
    muteProbability = channelData.get("muteProbability", 0)
    unmuteProbability = channelData.get("unmuteProbability", 0)
    
    text = (
        f"📢 <b>Channel Activity Details</b>\n"
        f"<b>Title:</b> <code>{channelTitle}</code>\n"
        f"<b>Invite Link:</b> <a href='{channelLink}'>{channelLink}</a>\n"
        f"<b>Status:</b> <code>{'✅ Enabled' if channelData.get('activityStatus', False) else '❎ Disabled'}\n\n</code>"
        f"<b>Join Delay:</b> <code>{minJoinDelay} - {maxJoinDelay}</code>\n"
        f"<b>Leave Delay:</b> <code>{minLeaveDelay} - {maxLeaveDelay}</code>\n\n"
        f"<b>Mute Probability:</b> <code>{muteProbability}%</code>\n"
        f"<b>Unmute Probability:</b> <code>{unmuteProbability}%</code>"
    )
    
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("✅ Enable" if not channelData.get("activityStatus", False) else "❎ Disable", callback_data=f"/ChannelActivityToggle {channelID}")],
            [InlineKeyboardButton("Join Delay", callback_data=f"nothing")],
            [InlineKeyboardButton("⏳ Min", callback_data=f"/changeMinJoinDelay {channelID}"),InlineKeyboardButton("⏳ Max", callback_data=f"/changeMaxJoinDelay {channelID}")],
            [InlineKeyboardButton("Leave Delay", callback_data=f"nothing")],
            [InlineKeyboardButton("⏳ Min", callback_data=f"/changeMinLeaveDelay {channelID}"),InlineKeyboardButton("⏳ Max", callback_data=f"/changeMaxLeaveDelay {channelID}")],
            [InlineKeyboardButton("Probability",callback_data="nothing")],
            [InlineKeyboardButton("🔕 Mute", callback_data=f"/changeMuteProbability {channelID}"),InlineKeyboardButton("🔕 Unmute",callback_data=f"/changeUnmuteProbability {channelID}")],
            [InlineKeyboardButton("🗑 Remove Channel", callback_data=f"/ChannelActivityDelete {channelID}")],
            [InlineKeyboardButton("<- Back", callback_data="/DailyActivityChannels 1")],
        ]
    )
    return text , keyboard
        
async def viewChannelManage(channelID, channelData=0):
    channelData = channelData or Channels.find_one({"channelID": channelID})
    validity = channelData.get("validity",False)
    daysLeft = channelData.get("daysLeft",0)
    if not channelData:
        return "❌ <b>Error: Channel not found!</b>", InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙 Back", callback_data="/manageChannels 1")]]
        )

    channelType = channelData.get('type', 'Unknown')
    channelLink = channelData.get('inviteLink', 'No invite link')
    channelUsername = channelData.get("username")
    channelTitle = channelData.get('title', 'Untitled Channel')
    servicesAdded = channelData.get("services", []) or []
    spamProtection = channelData.get("spamProtection", False)

    text = (
        f"📣 <b>CHANNEL DETAILS</b>\n\n"
        f"🆔 <b>ID:</b> <code>{channelID}</code>\n"
        f"🏷️ <b>Title:</b> <code>{channelTitle}</code>\n"
        f"🔖 <b>Type:</b> <code>{channelType}</code>\n"
        f"{f'📌 <b>Username:</b> <code>{channelUsername}</code>\n' if channelUsername else ''}"
        f"🔗 <b>Invite Link:</b> <a href='{channelLink}'>{channelLink}</a>\n\n"
        f"🔒 <b>Spam Protection:</b> {'✅ Enabled' if spamProtection else '❎ Disabled'}\n"
        f"⏳ <b>Validity:</b> {f"{'Expired!' if (not daysLeft) and validity else ('♾️ Permanent' if not validity else f'⌛ Temporary [{daysLeft} days left]')}"}\n\n"
    )


    if servicesAdded:
        text += f"⚙️ <b>Services:</b> {', '.join(servicesAdded)}"

    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(f"♻️ {"Enable" if not validity else "Disable"} Validity", callback_data=f"/toggle_validity {channelID}"),
            InlineKeyboardButton(f"➕ Add Days",f"/add_days {channelID}")],
            [InlineKeyboardButton(f"🔒 {"Enable" if not spamProtection else "Disable"} Spam Protection", callback_data=f"/toggle_spam_protection {channelID}")],
            [InlineKeyboardButton("⚙️ Auto Services", callback_data=f"/channelServices {channelID}")],
            [InlineKeyboardButton("🗑 Remove Channel", callback_data=f"/removeChannel {channelID}")],
            [InlineKeyboardButton("🔙 Back", callback_data="/manageChannels 1")]
        ]
    )

    return text, keyboard

    
async def selectReactionEmoji(channelID):
    syncBot: Client = await UserbotManager.getSyncBotClient()
    channelData = Channels.find_one({"channelID": int(channelID)})

    if not channelData:
        return "❌ <b>Error:</b> Channel not found!", InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙 Back", callback_data=f"/channelServices {channelID}")]]
        )
    chatInfo = await syncBot.get_chat(
        channelData.get("username") or channelData.get("inviteLink") or channelID
    )
    if not chatInfo.available_reactions: return "❌ <b>Reaction not allowed in channel</b>", InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙 Back", callback_data=f"/channelServices {channelID}")]]
        ) 
    if chatInfo.available_reactions.all_are_enabled:
        reactionEmojiArray = ["👍", "❤️", "😲", "😢", "😡", "🎉", "👏", "🔥", "🤔", "🙌", "💯", "✨", "🎶", "🕊️", "🌟"]
    else:
        reactionEmojiArray = [i.emoji for i in chatInfo.available_reactions.reactions]
    added_emojis = set(channelData.get("reactionsType", []))
    valid_emojis = added_emojis.intersection(reactionEmojiArray)
    if added_emojis != valid_emojis:
        Channels.update_one({"channelID": int(channelID)}, {"$set": {"reactionsType": list(valid_emojis)}})
    emoji_list = " ".join(valid_emojis) if valid_emojis else "No emojis added yet."
    text = (
        "🎭 <b>Manage Channel Reactions</b>\n\n"
        "📌 <b>Instructions:</b>\n"
        "• Select an emoji from the buttons below to <b>add</b> it to your channel reactions.\n"
        "• Select the same emoji again to <b>remove</b> it.\n\n"
        f"✅ <b>Currently Added Emojis:</b> <code>{emoji_list}</code>\n\n"
        "👇 <b>Choose emojis from the options below to customize your channel reactions.</b>"
    )
    keyboard_buttons = paginateArray(
        [InlineKeyboardButton(i, callback_data=f"/toggleEmoji {i} {channelID}") for i in reactionEmojiArray], 5
    )
    keyboard_buttons.append([InlineKeyboardButton("🔙 Back", callback_data=f"/channelServices {channelID}")])

    return text, InlineKeyboardMarkup(keyboard_buttons)

    
    
    

async def grantAccessMarkup(userID):
    accessUsers = Admin.find_one({"accessUser": True}) or {}
    usersList = accessUsers.get("list", [])
    text = f"🔑 <b>Manage Admin Access</b>\n\n"
    text += f"👤 <b>User ID:</b> <code>{userID}</code>\n\n"
    hasAccess = int(userID) in usersList
    buttonText = "✅ Grant Access" if not hasAccess else "❎ Remove Access"
    callbackData = f"/changeAccess {userID}"
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton(buttonText, callback_data=callbackData)]]
    )
    return text, keyboard



async def adminManageAccounts(page: int = 1, per_page: int = 10):
    allAccounts = list(Accounts.find({}))
    total_accounts = len(allAccounts)

    if total_accounts == 0:
        text = "<b>No accounts created yet.</b>"
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙 Back To Menu", callback_data="admin")]]
        )
        return text, keyboard

    # Pagination logic
    start = (page - 1) * per_page
    end = start + per_page
    accounts_to_display = allAccounts[start:end]
    total_pages = (total_accounts + per_page - 1) // per_page  # Calculate total pages

    # Construct the message text
    text = f"📂 <b>Manage Accounts (Page {page}/{total_pages}):</b>\n\n"
    
    
    keyboard_buttons = []
    for i, account in enumerate(accounts_to_display, start=start + 1):
        phone_number = account.get('phone_number', 'N/A')
        username = account.get('username', 'N/A')
        proxy = account.get("proxy", "N/A")
        isSync = account.get("syncBot", False)
        isHelper = account.get("helperBot",False)
        if isSync: role = "⚙ Syncer Bot"
        elif isHelper: role = "⚙ Helper Bot"
        else: role = ""
        
        keyboard_buttons.append([InlineKeyboardButton(f"{i}. {phone_number}", callback_data=f"/viewAccount {phone_number}")])

        account_info = (
            f"🔹 <b>Account [</b><code>{phone_number}</code><b>]: {role}</b>\n\n"
        )
        text += account_info

    # Navigation buttons
    navigation_buttons = []
    if page > 1:
        navigation_buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"/manageAccountListAdmin {page - 1}"))
    if page < total_pages:
        navigation_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"/manageAccountListAdmin {page + 1}"))
    
    #Skip to last or front
    if page == total_pages: skipButton = [InlineKeyboardButton("<-- First Page", callback_data=f"/manageAccountListAdmin 1")]
    else: skipButton = [InlineKeyboardButton("Last Page -->", callback_data=f"/manageAccountListAdmin {total_pages}")]
    # Back button
    back_button = [InlineKeyboardButton("🔙 Back To Menu", callback_data="admin")]

    # Combine all buttons
    keyboard = InlineKeyboardMarkup(keyboard_buttons + [navigation_buttons] + [skipButton] + [back_button])

    return text, keyboard


# For Admin
async def account_listings(fromUser):
    totalAccounts = Accounts.count_documents({})
    text = f"<b>📋 Manage Telegram Accounts</b>\n\n<b>Total Account:</b> <code>{totalAccounts}</code>\n\nHere, you can manage all Telegram accounts available for sale.\n\nChoose an option below to proceed."
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📄 View All Accounts",
                              callback_data="/manageAccountListAdmin")],
        [InlineKeyboardButton("➕ Add New Account",
                              callback_data="/add_account")],
        [InlineKeyboardButton("Add Session Files",callback_data="/add_session_file")],
        [InlineKeyboardButton("🔙 Back To Menu", callback_data="admin")]
    ])
    
    return text, keyboard

async def account_details_view(account_info, backCommand="/manageAccountListAdmin", langCode="english"):
    is_sync = account_info.get("syncBot", False)
    is_helper = account_info.get("helperBot", False)
    text = "<b>🔍 Account Details</b>\n\n"
    if is_sync: text += "<b>🛠️ Main Sync Manager Account</b>\n\n"
    elif is_helper: text += "<b>🛠️ Helper Sync Bot</b>\n\n"
    text += (
        f"<b>Phone Number:</b> <code>{account_info['phone_number']}</code>\n"
        f"<b>Username:</b> <a href='https://t.me/{account_info.get('username')}'>{account_info.get('username')}</a>\n"
        f"<b>Created At:</b> <code>{convertTime(account_info.get('added_at'))}</code>\n"
        f"<b>Session String:</b>\n<pre>{account_info['session_string']}</pre>\n\n"
        "Choose an action for this account:"
    )
    kb = []
    if not is_sync and not is_helper:
        kb.append([InlineKeyboardButton("🛠️ Assign As Main Sync Bot", callback_data=f"/assignAsSyncer {account_info['phone_number']}")])
    kb.append([InlineKeyboardButton("➕ Assign As Helper Bot" if not is_helper else "❌ Remove Helper Role", callback_data=f"/toggleHelperSync {account_info['phone_number']}")])
    kb.append([InlineKeyboardButton("🗑️ Remove Account", callback_data=f"/remove_account {account_info['phone_number']}")])
    kb.append([InlineKeyboardButton("↩️ Back", callback_data=backCommand)])
    return text, InlineKeyboardMarkup(kb)


def getAskWorkQuantity(text=None,task=None):
    numberAllowed = [2,10,20,30,40,50,100,300,"Manual"]
    buttons = InlineKeyboardMarkup(paginateArray([InlineKeyboardButton(str(i),f"/dynamicQuantity {task} {i}") for i in numberAllowed],3))
    if not text: text = "<b>👀 Enter work Quantity:</b>"
    return text , buttons

def getAskSpeed(task,text=None):
    numberAllowed = [0,1,5,10,25,50,60,"Manual"]
    buttons = InlineKeyboardMarkup(paginateArray([InlineKeyboardButton(str(i) if (i != 0) else "Instant",f"/dynamicSpeed {task} {i}") for i in numberAllowed],3))
    if not text: text = ("<b>⚡️ Enter The Speed Of The Work: ( In Seconds )</b>\n"
        "Instant = Instantly\n"
        "1 = Each 1 Second 1 user\n"
        "60 = Each 1 Minute 1 user")
    return text , buttons
    
import json

async def getAutoVotesMarkup(channelID):
    channelData = Channels.find_one({"channelID":int(channelID)})
    isAutoVote_enabled = channelData.get("isVoteEnabled",False)
    totalVotes = channelData.get("votesCount",[0])
    voteDelay = channelData.get("voteRestTime",[0])
    emptyOption = {i: 0 for i in range(10)}
    # optionsPercentage may be stored as a JSON string or as a dict in DB
    raw = channelData.get("optionsPercentage", emptyOption)
    if isinstance(raw, dict):
        loaded = raw
    elif isinstance(raw, str):
        try:
            loaded = json.loads(raw)
        except Exception:
            loaded = emptyOption
    else:
        loaded = emptyOption

    # Normalize keys to ints and ensure 0..9 exist
    optionsPerc = {}
    for k, v in loaded.items():
        try:
            nk = int(k)
        except Exception:
            continue
        try:
            nv = float(v)
            # show integer-like numbers as int
            if nv.is_integer():
                nv = int(nv)
        except Exception:
            nv = v
        optionsPerc[nk] = nv
    for i in range(10):
        optionsPerc.setdefault(i, 0)
    
    text = (
        f"<b>Automatic polling management</b>\n\n"
        f"<b>Status: {"Enabled" if isAutoVote_enabled else "Disabled"}</b>\n"
        f"<b>Total Votes:</b> <code>{totalVotes}</code> votes\n"
        f"<b>Delay:</b> <code>{voteDelay}</code> seconds\n"
    )
    
    text += "<b>Select Option to change percentage</b>"
    optionsButtonRows = paginateArray([
        InlineKeyboardButton(f"{int(i)+1}. {optionsPerc[i]}%", f"/setVotePercentage {channelID} {i}")
        for i in optionsPerc
    ])

    voteCountButton = [InlineKeyboardButton("Vote Count","/setVoteCount " + str(channelID))]
    delayButton = [InlineKeyboardButton("Delay", f"/setVoteDelay {channelID}")]
    
    toggleButton = [InlineKeyboardButton("Enable" if not isAutoVote_enabled else "Disable",f"/toggleAutoVote {channelID}")]
    backButton = [InlineKeyboardButton("<-- Back", f"/channelServices {channelID}")]
        
    keyboard = InlineKeyboardMarkup(
        optionsButtonRows + [toggleButton] + [voteCountButton,delayButton]  + [backButton]
    )
        
    return text,keyboard
    