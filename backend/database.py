import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
if not MONGODB_URI:
    raise ValueError("Missing MONGODB_URI in environment")

client = AsyncIOMotorClient(MONGODB_URI)
db = client.get_default_database()

# Assuming the default db is the one in the URI, e.g., 'historiar'
def get_db():
    return db
