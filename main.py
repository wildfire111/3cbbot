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
    for cog in cogs:
        await bot.load_extension(cog)
    utils.initialise_db()
    await bot.start(token)
    

@bot.event
async def on_ready():
    print("Bot online")
    user = await bot.fetch_user(248740105248964608)
    await user.send("Bot online.")
    await bot.tree.sync()
    


if __name__ == "__main__":
    asyncio.run(main())