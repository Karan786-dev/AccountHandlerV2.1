from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from database import Channels, Admin, Accounts
from functions import convertTime, paginateArray



def mainMenu(fromUser):
    text =  (f"<b>👋 Hello, {fromUser.first_name}!</b>\n\n")
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📩 Send Message","/sendMessage")],
        [InlineKeyboardButton("🔔 Join Chat","/joinChats"),InlineKeyboardButton("🔕 Leave Chats","/leaveChats")],
        [InlineKeyboardButton("👀 Views","/sendViews"),InlineKeyboardButton("❤️ Reaction","/sendReactions")],
        [InlineKeyboardButton("🗳 Votes","/sendVotes"),InlineKeyboardButton("Join Voice Chat","/joinVoiceChat")],
        [InlineKeyboardButton("Report Channel","/reportChat")],
        [InlineKeyboardButton("Manage Channels","/manageChannels")],
        [InlineKeyboardButton("📋 Telegram Accounts", callback_data="/manageAccountAdmin")],
        ])
    return text,keyboard

async def manageChannelServices(channelID):
    channelData = Channels.find_one({"channelID": int(channelID)})
    text = (
        "<b>Auto Services Configuration</b>\n\n"
        "📊 <b>Auto Views</b>:\n"
        f"- <b>Status</b>: {'Enabled' if channelData.get('isViewEnabled', False) else 'Disabled'}\n"
        f"- <b>Delay</b>: {channelData.get('viewRestTime', 0)} seconds\n"
        f"- <b>Views per Post</b>: {channelData.get('viewCount', 0)}\n\n"
        "🎭 <b>Auto Reactions</b>:\n"
        f"- <b>Status</b>: {'Enabled' if channelData.get('isReactionsEnabled') else 'Disabled'}\n"
        f"- <b>Delay</b>: {channelData.get('reactionRestTime')} seconds\n"
        f"- <b>Reactions per Post</b>: {channelData.get('reactionsCount')}\n"
        f"- <b>Reaction Emoji's</b>: {', '.join(channelData.get('reactionsType', []))}\n\n"
        f"🏤 <b>Auto Voice Join</b>\n"
        f"- <b>Status</b>: {'Enabled' if channelData.get('isVoiceEnabled') else 'Disabled'}\n"
        f"- <b>Delay</b>: {channelData.get('voiceRestTime',0)} seconds\n"
        f"- <b>Duration</b>: {channelData.get('voiceDuration',0)} seconds\n"
        f"- <b>Join Count</b>: {channelData.get('voiceCount',0)}\n\n"
        "Use the buttons below to update your auto services preferences."
    )
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔽 Views","nothing")
        ],
        [
            InlineKeyboardButton("Delay", callback_data=f"/changeDelay views {channelID}"),
            InlineKeyboardButton("Per Post", callback_data=f"/changeCount views {channelID}"),
            InlineKeyboardButton('❎ Disable' if channelData.get('isViewEnabled') else '✅ Enable', callback_data=f"/toggle_views {channelID}"),
        ],
        [
            InlineKeyboardButton("🔽 Reactions","nothing")    
        ],
        [
            InlineKeyboardButton("Delay", callback_data=f"/changeDelay reactions {channelID}"),
            InlineKeyboardButton("Per Post", callback_data=f"/changeCount reactions {channelID}"),
            InlineKeyboardButton('❎ Disable' if channelData.get('isReactionsEnabled') else '✅ Enable', callback_data=f"/toggle_reactions {channelID}"),
        ],
        [
            InlineKeyboardButton("Reaction Emoji's", callback_data=f"/reactionEmoji {channelID}"),
        ],
        [
            InlineKeyboardButton("🔽 Voice Join","nothing")
        ],
        [
            InlineKeyboardButton("Delay", callback_data=f"/changeDelay voice {channelID}"),
            InlineKeyboardButton("Join Count", callback_data=f"/changeJoinCount {channelID}"),
            InlineKeyboardButton('❎ Disable' if channelData.get('isVoiceEnabled') else '✅ Enable', callback_data=f"/toggle_voice {channelID}"),
        ],
        [
            InlineKeyboardButton("Duration", callback_data=f"/changeDuration {channelID}"),    
        ],
        [
            InlineKeyboardButton("🔙 Back", callback_data=f"/viewChannel {channelID}"),
            InlineKeyboardButton("🔙 Main Menu", callback_data="/main_menu"),
        ]
    ])
    return text, keyboard


#For Admin
async def manageChannelMarkup(page: int = 1, per_page: int = 5):
    allChannels = list(Channels.find({})) or []
    totalChannels = len(allChannels)
    backButton = InlineKeyboardButton("Back","/main_menu")
    addChannelButton = InlineKeyboardButton("Add Channel","/addChannel")
    if totalChannels == 0:
        text = "<b>No any Channels Added Yet\nUse below button to add new channels</b>"
        keyboard = InlineKeyboardMarkup(
            [
                [addChannelButton],
                [backButton]
            ]
        )
        return text , keyboard
    # Pagination logic
    start = (page - 1) * per_page
    end = start + per_page
    channelsToDisplay = allChannels[start:end]
    total_pages = (totalChannels + per_page - 1) // per_page  # Calculate total pages

    # Navigation buttons
    keyboard_buttons = []
    # Construct the message text
    text = f"<b>Manage Channels </b>(Page {page}/{total_pages}):\n<b>Select Channel</b> from below buttons\n"
    for i, channelData in enumerate(channelsToDisplay, start=start + 1):
        keyboard_buttons.append(InlineKeyboardButton(f"{i}. {channelData.get("username") or channelData.get("channelID")}",f"/viewChannel {channelData.get("channelID")}"))

    #Navigation Button 
    navigationButton = []
    if page > 1:
        navigationButton.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"/manageChannels {page - 1}"))
    if page < total_pages:
        navigationButton.append(InlineKeyboardButton("Next ➡️", callback_data=f"/manageChannels {page + 1}"))

    moreButtons = [addChannelButton,backButton]
    keyboard = InlineKeyboardMarkup([keyboard_buttons,navigationButton,moreButtons])

    return text, keyboard
        
        
        
async def viewChannelManage(channelID,channelData=0):
    channelData = channelData or Channels.find_one({"channelID": channelID})
    channelType = channelData.get('type')
    channelLink = channelData.get('inviteLink')
    channelUsername = channelData.get("username")
    channelTitle = channelData.get('title')
    servicesAdded = channelData.get("services",[])
    text = (
        f"<b>Channel ID: </b><code>{channelID}</code>\n\n"
        f"<b>Title: </b><code>{channelTitle}</code>\n"
        f"<b>Type: </b><code>{channelType}</code>\n"
        f"{f'<b>Username: </b><code>{channelUsername}</code>\n' if channelUsername else ''}"
        f"<b>Invite Link: <a href='{channelLink}'>{channelLink}</a></b>\n"
    )
    if len(servicesAdded): text += f"<b>Services: </b>{','.join(servicesAdded)}"
    
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Auto Services",f"/channelServices {channelID}"),
            ] ,
            [
                InlineKeyboardButton("Remove Channel",f"/removeChannel {channelID}"),
            ],
            [
                InlineKeyboardButton("Back","/manageChannels 1")
            ]
        ]
    )
    return text , keyboard

    
async def selectReactionEmoji(channelID,):
    reactionEmojiArray = ["👍", "❤️", "😂", "😮", "😢", "👏", "🔥", "🎉", "💯", "🤔","🤩", "😡", "😎", "🎶", "🥳", "💔", "✨", "🚀", "🌈", "🍿"]
    channelData = Channels.find_one({"channelID":int(channelID)})
    added_emojis = channelData.get("reactionsType", [])
    emoji_list = ",".join(added_emojis) if added_emojis else "No emojis added yet."

    text = (
        "<b>Manage Channel Reactions</b>\n\n"
        "🎭 <b>Instructions:</b>\n"
        "- Select an emoji from the buttons below to <b>add</b> it to your channel reactions.\n"
        "- Select the same emoji again to <b>remove</b> it from your channel reactions.\n\n"
        f"✅ <b>Currently Added Emojis:</b> <code>{emoji_list}</code>\n\n"
        "Choose emojis from the options below to customize your channel reactions."
    )
    keyboardButton = paginateArray([InlineKeyboardButton(i,f"/toggleEmoji {i} {channelID}") for i in reactionEmojiArray],5)
    keyboardButton.append([InlineKeyboardButton("🔙 Back", callback_data=f"/channelServices {channelID}")])
    return text , InlineKeyboardMarkup(keyboardButton)
    
    
    
    

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
    text = "<b>Welcome, Admin!\nSelect a section to manage the bot and its users.</b>"
    keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("⚙️ Grant Access", callback_data="/grantAccess")],
    
    ])
    return text,keyboard



# For Admin
async def adminManageAccounts(page: int = 1, per_page: int = 5):
    allAccounts = list(Accounts.find({}))
    total_accounts = len(allAccounts)
    if total_accounts == 0:
        text = (
            f"{"<b>No accounts created yet.<b>"}"
            )
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙 Back To Menu", callback_data=f"admin")]]
        )
        return text, keyboard

    # Pagination logic
    start = (page - 1) * per_page
    end = start + per_page
    accounts_to_display = allAccounts[start:end]
    total_pages = (total_accounts + per_page - 1) // per_page  # Calculate total pages

    # Navigation buttons
    keyboard_buttons = []
    # Construct the message text
    text = f"<b>Manage Accounts (Page {page}/{total_pages}):</b>\n\n"
    for i, account in enumerate(accounts_to_display, start=start + 1):
        keyboard_buttons.append(InlineKeyboardButton(f"{i}. {account.get('phone_number')}",f"/viewAccount {account.get('phone_number')}"))
        account_info = (
            f"<b>🔹 Account {i}:</b>\n"
            f"<b>Username:</b> <code>{account.get('username', 'N/A')}</code>\n"
            f"<b>Phone Number: {account.get('phone_number','N/A')}</b>\n\n"
        )
        text += account_info

    #Navigation Button 
    navigationButton = []
    if page > 1:
        navigationButton.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"/account_listings {page - 1}"))
    if page < total_pages:
        navigationButton.append(InlineKeyboardButton("Next ➡️", callback_data=f"/account_listings {page + 1}"))

    # Back button
    backButton = [InlineKeyboardButton("🔙 Back To Menu", callback_data=f"admin")]
    keyboard = InlineKeyboardMarkup([keyboard_buttons,navigationButton,backButton])

    return text, keyboard


# For Admin
async def account_listings(fromUser):
    text = "<b>📋 Manage Telegram Accounts</b>\n\nHere, you can manage all Telegram accounts available for sale.\n\nChoose an option below to proceed."
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📄 View All Accounts",
                              callback_data="/manageAccountListAdmin")],
        [InlineKeyboardButton("➕ Add New Account",
                              callback_data="/add_account")],
        [InlineKeyboardButton("🔙 Back To Menu", callback_data="admin")]
    ])
    
    return text, keyboard

#For Admin
async def account_details_view(account_info,backCommand="/manageAccountListAdmin",langCode="english"):
    # Display account details
    text = (
        "<b>🔍 Account Details</b>\n\n"
        f"{'<b>🛠️ Sync Manager Account</b>\n\n' if account_info.get("syncBot",False) else ""}"
        f"<b>Phone Number: </b><code>{account_info['phone_number']}</code>\n"
        f"<b>Username: <a href='https://t.me/{account_info.get('username')}'>{account_info.get('username')}</a></b>\n"
        f"<b>Created AT: </b><code>{convertTime(account_info.get('added_at'))}</code>\n"
        f"<b>String Session:</b> <pre>{account_info["session_string"]}</pre>\n"
        "Choose an action for this account."
    )
    roleAssignButton = [InlineKeyboardButton("🛠️ Assign Sync Role",callback_data=f"/assignAsSyncer {account_info["phone_number"]}")]
    keyboard = [
        roleAssignButton,
        [InlineKeyboardButton("🗑️ Remove Account", callback_data=f"/remove_account {account_info['phone_number']}")],
        [InlineKeyboardButton("↩️ Back",callback_data=backCommand)],
    ]
    if account_info.get("syncBot",False): keyboard.pop(keyboard.index(roleAssignButton))
    return text, InlineKeyboardMarkup(keyboard)

