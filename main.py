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
#print(token)

intents = discord.Intents.all()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)
bot.state = 'startup'
cogs = ['cogs.entries','cogs.controls','cogs.voting']

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
    # try:
    #     await bot.tree.sync() #UNCOMMENT BEFORE PROD
    # except Exception as e:
    #     ValueError(f"Sync error: {e}")
    bot.battles = []
    bot.entries = {}
    print("Loading DB")
    utils.load_entries_from_db(bot)
    print("Loading state")
    utils.load_timeline_values(bot)
    print("Starting archivist")
    asyncio.create_task(utils.archivist(bot))
    print("startup complete")
    


if __name__ == "__main__":
    asyncio.run(main())