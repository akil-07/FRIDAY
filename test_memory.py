import os
from dotenv import load_dotenv
from groq import Groq
from pymongo import MongoClient

load_dotenv()
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
# Hardcode the confirmed Mongo URI for the test
MONGO_URI = 'mongodb+srv://akilsudhagar7:Akil2112@cluster0.hvpawkq.mongodb.net/?appName=Cluster0'

print("1. Connecting to MongoDB...")
db_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = db_client["friday_db"]
collection = db["core_profile"]

print("2. Simulating a conversation...")
user_text = "I am currently working on building a super advanced AI assistant named Friday. Also, my favorite car is a Porsche."
ai_response = "Understood, Boss. I will keep that in mind for our future interactions."

print("3. Connecting to Groq and running Extraction Engine...")
groq_client = Groq(api_key=GROQ_API_KEY)
extract_prompt = f"""
Analyze this interaction between the user and Friday. 
User: {user_text}
Friday: {ai_response}
Extract any permanent facts, preferences, or personal details about the user. 
If none exist, output EXACTLY 'NONE'. If facts exist, output a short bulleted list.
"""

completion = groq_client.chat.completions.create(
    model="qwen/qwen3.8-27b",
    messages=[{"role": "user", "content": extract_prompt}]
)

facts = completion.choices[0].message.content.strip()
print(f"\n--- Extracted Facts ---\n{facts}\n-----------------------\n")

if facts != "NONE" and facts != "":
    print("4. Saving facts to MongoDB...")
    collection.insert_one({"fact": facts})
    print("SUCCESS: Facts saved to database!")
else:
    print("No facts extracted.")

print("\n5. Reading Current Core Profile from MongoDB:")
docs = collection.find()
for doc in docs:
    print(f"- {doc['fact']}")
