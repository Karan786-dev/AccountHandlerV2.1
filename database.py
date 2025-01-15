from pymongo import MongoClient  # type: ignore
from config import MONGO_URL


try:
    client = MongoClient(MONGO_URL)
    mydb = client['AccountHandlerBotV2']
    Admin = mydb['admin']
    Users = mydb['users']
    Accounts = mydb['accounts']
    Transactions = mydb["Transactions"]
    Channels = mydb["channels"]
except Exception as e:
    print("Error connecting to MongoDB: ", e)
