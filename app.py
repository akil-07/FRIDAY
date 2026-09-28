import os
import aiohttp
from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import Response, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from groq import Groq
from pymongo import MongoClient

load_dotenv()
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
DEEPGRAM_API_KEY = os.getenv('DEEPGRAM_API_KEY')
MONGO_URI = os.getenv('MONGO_URI')

groq_client = Groq(api_key=GROQ_API_KEY)
app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

# Connect to MongoDB (Long-Term Memory)
db_client = None
collection = None
if MONGO_URI:
    try:
        db_client = MongoClient(MONGO_URI)
        db = db_client["friday_db"]
        collection = db["core_profile"]
    except Exception as e:
        print("Failed to connect to MongoDB:", e)

# Short-Term Memory (Rolling Window)
short_term_memory = []

def extract_memory_background(user_text: str, ai_response: str):
    if collection is None: return
    extract_prompt = f"""
    Analyze this interaction between the user and Friday. 
    User: {user_text}
    Friday: {ai_response}
    Extract any permanent facts, preferences, or personal details about the user. 
    If none exist, output EXACTLY 'NONE'. If facts exist, output a short bulleted list.
    """
    try:
        completion = groq_client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[{"role": "user", "content": extract_prompt}]
        )
        facts = completion.choices[0].message.content.strip()
        if facts != "NONE" and facts != "":
            collection.insert_one({"fact": facts})
    except Exception as e:
        print("Memory extraction error:", e)

@app.get("/")
async def get_index():
    with open("static/index.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.post("/chat")
async def chat(background_tasks: BackgroundTasks, audio: UploadFile = File(...), brain: str = Form("fast")):
    audio_data = await audio.read()
        
    # EARS (No disk I/O, direct memory transfer)
    transcription = groq_client.audio.transcriptions.create(
        file=(audio.filename, audio_data),
        model="whisper-large-v3",
    )
    user_text = transcription.text
    if not user_text.strip():
        return Response(status_code=400, content="No speech detected")
        
    # Fetch Core Profile from DB
    core_profile = ""
    if collection is not None:
        docs = collection.find()
        facts_list = [doc["fact"] for doc in docs]
        if facts_list:
            core_profile = "Facts about the Boss:\n" + "\n".join(facts_list)

    # Select Model
    model_id = "openai/gpt-oss-120b" if brain == "genius" else "qwen/qwen3.8-27b"

    system_prompt = f"""You are Friday, my highly advanced and loyal AI assistant. I am your boss and creator. Address me as 'Boss' or 'Sir'. Be extremely sharp, highly competent, and obedient, similar to JARVIS from Iron Man. Speak in a crisp, professional, yet slightly witty tone. Keep your answers EXTREMELY short (1 sentence max). Do not use emojis. 
    
    {core_profile}"""

    messages = [{"role": "system", "content": system_prompt}]
    
    # Inject Short-Term Memory (last 6 messages = 3 conversational turns)
    for msg in short_term_memory[-6:]:
        messages.append(msg)

    # Inject current input
    messages.append({"role": "user", "content": user_text})

    # BRAIN
    completion = groq_client.chat.completions.create(
        model=model_id,
        messages=messages
    )
    ai_response = completion.choices[0].message.content

    # Update Short-Term Memory
    short_term_memory.append({"role": "user", "content": user_text})
    short_term_memory.append({"role": "assistant", "content": ai_response})

    # Trigger Background Task for Long-Term Memory Extraction
    background_tasks.add_task(extract_memory_background, user_text, ai_response)

    # MOUTH
    url = "https://api.deepgram.com/v1/speak?model=aura-asteria-en"
    headers = {
        "Authorization": f"Token {DEEPGRAM_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {"text": ai_response}
    
    async def stream_audio():
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as resp:
                if resp.status == 200:
                    async for chunk in resp.content.iter_chunked(4096):
                        yield chunk

    return StreamingResponse(stream_audio(), media_type="audio/mpeg")
