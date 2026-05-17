from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

# Load env variables
load_dotenv()

# MongoDB URL from .env
MONGO_URL = os.getenv("MONGODB_URI", "mongodb://localhost:27017")

client = AsyncIOMotorClient(MONGO_URL)

db = client["ai_todo_app"]      # database name
todo_collection = db["todos"]  # collection