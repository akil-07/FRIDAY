import os
from dotenv import load_dotenv
import aiohttp
import asyncio
from groq import Groq
from duckduckgo_search import DDGS

load_dotenv()

async def test_deepgram():
    print("Testing Deepgram...")
    DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
    if not DEEPGRAM_API_KEY:
        print("ERROR: DEEPGRAM_API_KEY not found in .env")
        return
    
    tts_url = "https://api.deepgram.com/v1/speak?model=aura-asteria-en"
    headers = {"Authorization": f"Token {DEEPGRAM_API_KEY}"}
    payload = {"text": "This is a test of the Deepgram API."}
    
    async with aiohttp.ClientSession() as session:
        async with session.post(tts_url, headers=headers, json=payload) as tts_resp:
            print(f"Deepgram Status: {tts_resp.status}")
            data = await tts_resp.read()
            if tts_resp.status != 200:
                print(f"Deepgram Error Response: {data}")
            else:
                print("Deepgram: SUCCESS (Audio data received)")

def test_duckduckgo():
    print("\nTesting DuckDuckGo...")
    try:
        results = DDGS().text("price of bitcoin", max_results=3)
        search_str = "\n".join([f"- {r['title']}" for r in results])
        print(f"DuckDuckGo SUCCESS: Found {len(list(results))} results.")
    except Exception as e:
        print(f"DuckDuckGo ERROR: {e}")

async def main():
    await test_deepgram()
    test_duckduckgo()

if __name__ == "__main__":
    asyncio.run(main())
