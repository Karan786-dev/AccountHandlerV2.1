from pyrogram.types import ReplyKeyboardMarkup, KeyboardButton  # type: ignore

API_ID = "3269267"
API_HASH = "d23d55a7cf2c18966a1b252250754a58"

# BOT_TOKEN = "7029370863:AAFtzllTGtEbSMZe6lwH8krXndadVXNNDSc"

# Main Bot
BOT_TOKEN = "7328516884:AAFsGmhhWXTurLAdVXpC5zDci_QwUJPMxpU"

# Booster Bot
BOT_TOKEN_BOOSTER = "7765567906:AAFUOgHS39ILhBNEy2HUp4yNW2RNR6WtQtg"
#Database
MONGO_URL = "mongodb+srv://karan:karan@cluster0.rs3oz.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "AccountHandlerBotV2_YOGI"

ADMINS = [6852042577,6037874119,1468386562,589062096]

#Restart pending tasks from tasksData Folder
restart_pending_tasks = True

#Contact Admin 
adminUsername = "https://t.me/Yogi_youtuber"

# Session files
USERBOT_SESSION = "sessions/userbots"
SESSION = "sessions/mainBot"

# Logging Channels
UPLOADING_CHANNEL = "@yogi_logs"
LOGGING_CHANNEL = "@aYogi_logs"

# Cancel Button
cancelButtonText = "🚫 Cancel"
cancelKeyboard = ReplyKeyboardMarkup([[KeyboardButton(cancelButtonText)]], resize_keyboard=True, one_time_keyboard=True)