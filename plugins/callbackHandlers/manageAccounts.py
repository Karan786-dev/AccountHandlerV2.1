from pyrogram import Client, filters  # type: ignore
from markups import adminManageAccounts, account_listings, account_details_view
from database import Accounts 
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton , CallbackQuery , ReplyKeyboardRemove# type: ignore
from orderAccounts import UserbotManager


@Client.on_callback_query(filters.regex(r'^/manageAccountAdmin'))
async def adminManageAccountsCallback(_, query):
    text, keyboard = await account_listings(query.from_user)
    await query.message.edit(text, reply_markup=keyboard)
    pass


@Client.on_callback_query(filters.regex(r'^/manageAccountListAdmin'))
async def adminManageAccountsListCallback(_, query):
    dataSplit = query.data.split(maxsplit=1)
    page = int(dataSplit[1]) if len(dataSplit) > 1 else 1
    text, keyboard = await adminManageAccounts(page)
    await query.message.edit(text, reply_markup=keyboard)
    pass


@Client.on_callback_query(filters.regex(r'^/viewAccount'))
async def adminViewAccount(_, query):
    phone_number = query.data.split(maxsplit=1)[1]
    accountDetails = Accounts.find_one({"phone_number": phone_number})
    text, keyboard = await account_details_view(accountDetails)
    await query.message.edit(text, reply_markup=keyboard)

@Client.on_callback_query(filters.regex(r'^/assignAsSyncer'))
async def assignAsSyncerHandler(_,query:CallbackQuery):
    phone_number = query.data.split(maxsplit=1)[1]
    text = f"🚨 Are you sure to assign this account as syncer bot\nThis bot will join all added channels and receive new messages from those channels\n\n<b>Make sure you login this account in your device</b>"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ No", f"/viewAccount {phone_number}"),
         InlineKeyboardButton("✅ Yes", f"/confirmAssignAsSyncer {phone_number}")]
    ])
    await query.message.edit(text,reply_markup=keyboard)
    
@Client.on_callback_query(filters.regex(r'^/confirmAssignAsSyncer'))
async def assignAsSyncerConfirmHandler(_,query:CallbackQuery):
    phone_number = query.data.split(maxsplit=1)[1]
    oldSyncBot = Accounts.find_one({"syncBot":True})
    if oldSyncBot and oldSyncBot.get("phone_number") == phone_number: return await query.answer("This account is already assigned as syncer")
    if oldSyncBot:Accounts.update_one({"phone_number":oldSyncBot.get("phone_number")},{"$unset":{"syncBot":True}})
    updateData = Accounts.find_one_and_update({"phone_number":phone_number},{"$set":{"syncBot":True}},return_document=True)
    await query.message.edit("Assigning To Sync Bot...")
    oldSyncBotClient: Client = UserbotManager.getSyncBotClient()
    if oldSyncBotClient.is_connected: await UserbotManager.stop_client(oldSyncBot.get("phone_number"))
    await UserbotManager.start_client(updateData.get("session_string"),updateData.get("phone_number"),isSyncBot=True)
    text , keyboard = await account_details_view(updateData)
    await query.message.edit(text,reply_markup=keyboard)
    
    

@Client.on_callback_query(filters.regex(r'^/remove_account'))
async def removeAccount(_, query):
    phone_number = query.data.split(maxsplit=1)[1]
    text = f"🚨 Are you sure you want to delete your account?\n\nAll your data will be permanently removed and cannot be recovered. This action is irreversible.\n\n<b>⚠️ Proceed with caution!</b>"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Cancel", f"/cancelDeleteAccount {phone_number}"),
         InlineKeyboardButton("🗑️ Delete", f"/confirmRemoval {phone_number}")]
    ])
    await query.message.edit(text, reply_markup=keyboard)


@Client.on_callback_query(filters.regex(r'^/confirmRemoval'))
async def confirmAccountRemove(_, query):
    phone_number = query.data.split(maxsplit=1)[1]
    Accounts.delete_one({"phone_number": phone_number})
    await query.message.edit(
        "✅ Account has been successfully deleted.",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("↩️ Back to Listings",
                                   callback_data="/manageAccountListAdmin")]]
        )
    )


@Client.on_callback_query(filters.regex(r'^/cancelDeleteAccount'))
async def cancelDeleteAccount(_, query):
    phone_number = query.data.split(maxsplit=1)[1]
    accountDetails = Accounts.find_one({"phone_number": phone_number})
    text, keyboard = await account_details_view(accountDetails)
    await query.message.edit(text, reply_markup=keyboard)

@Client.on_callback_query(filters.regex(r'^/removeProxy'))
async def removeProxyCallback(_,query:CallbackQuery):
    phone_number = query.data.split(maxsplit=1)[1]
    await query.answer(f"Proxy Removed From {phone_number}")
    Accounts.update_one({"phone_number":phone_number},{"$unset":{"proxy":True}})
    await query.message.edit_reply_markup(ReplyKeyboardRemove())