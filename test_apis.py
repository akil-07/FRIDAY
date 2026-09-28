import os
import asyncio
from dotenv import load_dotenv
from groq import Groq
import aiohttp

load_dotenv()
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
DEEPGRAM_API_KEY = os.getenv('DEEPGRAM_API_KEY')

async def test_all():
    print("1. Testing Groq (Brain)...")
    groq_client = Groq(api_key=GROQ_API_KEY)
    try:
        completion = groq_client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[{"role": "user", "content": "Say 'hello world'"}]
        )
        ai_response = completion.choices[0].message.content
        print(f"Groq Success! Response: {ai_response}")
    except Exception as e:
        print(f"Groq Failed: {e}")
        return

    print("2. Testing Deepgram (Mouth)...")
    url = "https://api.deepgram.com/v1/speak?model=aura-asteria-en"
    headers = {
        "Authorization": f"Token {DEEPGRAM_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {"text": ai_response}
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as resp:
            if resp.status == 200:
                print("Deepgram Success! HTTP 200 OK")
            else:
                error_text = await resp.text()
                print(f"Deepgram Failed: HTTP {resp.status} - {error_text}")
                return
    
    print("🎉 ALL SYSTEMS GO!")

if __name__ == "__main__":
    asyncio.run(test_all())
