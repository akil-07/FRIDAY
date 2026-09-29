import os
import asyncio
from groq import Groq
from duckduckgo_search import DDGS
from dotenv import load_dotenv

load_dotenv()
groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))
user_text = "what is the weather right now in New York"

routing_prompt = f"""
Does this user's statement require looking up real-time, live internet information (like current weather, news, sports scores, recent events, or stock prices)?
User: "{user_text}"
If it DOES require live data, output exactly the best search query to find it. Do not output anything else.
If it DOES NOT require live data, output EXACTLY the word 'NO'.
"""
router = groq_client.chat.completions.create(
    model="qwen/qwen3.8-27b",
    messages=[{"role": "user", "content": routing_prompt}],
    temperature=0
)
search_query = router.choices[0].message.content.strip()
print("Search query:", search_query)

if search_query != "NO":
    results = list(DDGS().text(search_query, max_results=3))
    print("DDG Results:")
    for r in results:
        print(f"- {r['title']}: {r['body']}")
