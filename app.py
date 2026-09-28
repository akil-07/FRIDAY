import os
import aiohttp
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import Response, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
DEEPGRAM_API_KEY = os.getenv('DEEPGRAM_API_KEY')

groq_client = Groq(api_key=GROQ_API_KEY)
app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def get_index():
    with open("static/index.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.post("/chat")
async def chat(audio: UploadFile = File(...), brain: str = Form("fast")):
    audio_data = await audio.read()
        
    # EARS (No disk I/O, direct memory transfer)
    transcription = groq_client.audio.transcriptions.create(
        file=(audio.filename, audio_data),
        model="whisper-large-v3",
    )
    user_text = transcription.text
    if not user_text.strip():
        return Response(status_code=400, content="No speech detected")
        
    # Select Model
    model_id = "openai/gpt-oss-120b" if brain == "genius" else "qwen/qwen3.8-27b"

    # BRAIN
    completion = groq_client.chat.completions.create(
        model=model_id,
        messages=[
            {"role": "system", "content": "You are Friday, my highly advanced and loyal AI assistant. I am your boss and creator. Address me as 'Boss' or 'Sir'. Be extremely sharp, highly competent, and obedient, similar to JARVIS from Iron Man. Speak in a crisp, professional, yet slightly witty tone. Keep your answers EXTREMELY short (1 sentence max). Do not use emojis."},
            {"role": "user", "content": user_text}
        ]
    )
    ai_response = completion.choices[0].message.content

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
