import os
import discord
from dotenv import load_dotenv
import asyncio
from groq import Groq
import aiohttp
import imageio_ffmpeg

# Setup Keys
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
DEEPGRAM_API_KEY = os.getenv('DEEPGRAM_API_KEY')

# Initialize AI Clients
groq_client = Groq(api_key=GROQ_API_KEY)

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Bot(intents=intents)

# FIX PYCORD VOICE BUG
if not hasattr(discord.sinks.WaveSink, '__sink_listeners__'):
    discord.sinks.WaveSink.__sink_listeners__ = []

# This magically gets the ffmpeg audio driver without you having to install it manually!
FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('Friday is fully online with Voice AI capabilities!')

@bot.slash_command(name="join", description="Tell Friday to join your voice channel")
async def join(ctx):
    if not ctx.author.voice:
        await ctx.respond("You need to be in a voice channel first!")
        return
    channel = ctx.author.voice.channel
    await ctx.respond(f"Joining {channel.name}... 🎙️")
    await channel.connect()

@bot.slash_command(name="leave", description="Tell Friday to leave the voice channel")
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.respond("Disconnected. Goodbye!")
    else:
        await ctx.respond("I'm not in a voice channel.")

@bot.slash_command(name="ask", description="Ask Friday a question (She will speak the answer!)")
async def ask(ctx, question: str):
    if not ctx.voice_client:
        await ctx.respond("I am not in a voice channel! Use /join first.")
        return

    await ctx.respond(f"**You asked:** {question}\n*Thinking... 🧠*")
    
    user_text = question

    # 3. Think with Groq (Brain)
    completion = groq_client.chat.completions.create(
        model="qwen/qwen3.8-27b",
        messages=[
            {"role": "system", "content": "You are Friday, a highly advanced personal AI assistant. Keep responses under 3 sentences. Be conversational and helpful."},
            {"role": "user", "content": user_text}
        ]
    )
    ai_response = completion.choices[0].message.content
    await ctx.send(f"**Friday:** {ai_response}")

    # 4. Speak with Deepgram (Mouth)
    audio_output = "response.mp3"
    url = "https://api.deepgram.com/v1/speak?model=aura-asteria-en"
    headers = {
        "Authorization": f"Token {DEEPGRAM_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {"text": ai_response}
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as resp:
            if resp.status == 200:
                with open(audio_output, "wb") as f:
                    f.write(await resp.read())
            else:
                print(f"Deepgram Error: {await resp.text()}")

    # 5. Play audio back into the Discord channel
    source = discord.FFmpegPCMAudio(executable=FFMPEG_EXE, source=audio_output)
    ctx.voice_client.play(source)

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
