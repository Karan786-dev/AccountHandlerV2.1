# Telegram Bot (Pyrofork-based)

A powerful Telegram bot built using [Pyrofork](https://github.com/pyrogram/pyrogram) that automates various tasks such as sending bulk messages, managing reactions, joining channels, handling auto-views, and participating in live streams.

## Features

- **Bulk Messaging**: Send messages to multiple users with or without images.
- **Automated Views & Reactions**: Automatically add views and reactions to posts.
- **Auto Voting**: Participate in Telegram polls automatically.
- **Channel Management**:
  - Join and leave channels.
  - Auto-engagement with posts (views, reactions, votes).
  - Live stream participation.
- **Voice Chat Management**:
  - Join voice chats in channels.
  - Auto-join live streams when they start.
- **Multi-Account Support**: Add multiple accounts to perform tasks.
- **Auto Tasks Configuration**: Customize automated tasks for different channels.
- **Real-time Monitoring**: Track bot actions and task performance.

## Installation

### Requirements
- Python 3.8+
- A Telegram API ID & API Hash (Get from [my.telegram.org](https://my.telegram.org/))
- Pyrogram (Pyrofork) installed
- MongoDB (for storing account and task data)

### Setup
1. Clone the repository:
   ```sh
   git clone https://github.com/yourusername/yourrepo.git
   cd yourrepo
   ```
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
3. Configure environment variables or `config.py`:
   ```python
   from pyrogram.types import ReplyKeyboardMarkup, KeyboardButton

   API_ID = "your_api_id"
   API_HASH = "your_api_hash"
   BOT_TOKEN = "your_telegram_bot_token"
   
   # Database
   MONGO_URL = "your_mongodb_connection_string"
   DB_NAME = "AccountHandlerBot"
   
   # Admin Settings
   ADMINS = [6852042577, 6037874119, 1468386562, 589062096]
   adminUsername = "https://t.me/karan_pb_30"
   
   # Logging Channels
   UPLOADING_CHANNEL = ""
   LOGGING_CHANNEL = ""
   ```
5. Create Enviroment
   ```
   bash createEnv.sh
   ```
4. Run the bot:
   ```
   bash startBot.sh
   ```

## Usage
- Use `/start` to initialize the bot.
- Use `/admin` to access admin panel.
- Add accounts using the provided bot commands.
- Configure auto-tasks via the settings menu.
- Monitor tasks and logs in log channel.


## Contact
For support or feature requests, open an issue or contact me on Telegram: [@karan_pb_30](https://t.me/karan_pb_30).

