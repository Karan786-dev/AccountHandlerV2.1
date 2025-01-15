from pyrogram.types import ReplyKeyboardMarkup, KeyboardButton  # type: ignore

API_ID = "3269267"
API_HASH = "d23d55a7cf2c18966a1b252250754a58"

BOT_TOKEN = "8078435032:AAHa2zUb9DOiCFseLdeJmJrx5-KbgrE8_2k"
MONGO_URL = "mongodb+srv://karan:karan@cluster0.rs3oz.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
ADMINS = [1468386562, 6568376766]

# Session files
USERBOT_SESSION = "sessions/userbots"
SESSION = "sessions/mainBot"

# Deposit Accept Payment Gateway Plisio

# Cancel Button
cancelButtonText = "Cancel"
cancelKeyboard = ReplyKeyboardMarkup(
    [[KeyboardButton(cancelButtonText)]], resize_keyboard=True, one_time_keyboard=True)