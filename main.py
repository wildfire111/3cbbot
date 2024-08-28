import discord
from discord.ext import commands
from discord.utils import get
import sqlite3
import asyncio
import logging
import requests
import os
from dotenv import load_dotenv
import utils

load_dotenv()
#print("Environment variables loaded:", os.environ)
token = os.getenv('BOT_KEY')
print(token)

intents = discord.Intents.all()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)
bot.state = 'startup'
cogs = ['cogs.entries','cogs.controls']

async def main():
    print("Bot starting")
    for cog in cogs:
        try:
            await bot.load_extension(cog)
            print(f"Loaded {cog}")
        except Exception as e:
            print(f"Failed to load {cog}: {e}")
    utils.initialise_db()
    await bot.start(token)
    

@bot.event
async def on_ready():
    bot.state = 'startup'
    print("Synching commands")
    # user = await bot.fetch_user(248740105248964608)
    # await user.send("Bot online.")
    await bot.tree.sync()
    print("Loading DB")
    utils.load_entries_from_db(bot)
    print("Starting DB management task")
    asyncio.create_task(utils.add_entries_to_db(bot))
    bot.state = 'entriesopen'
    print(f"Bot state: {bot.state}")
    


if __name__ == "__main__":
    asyncio.run(main())