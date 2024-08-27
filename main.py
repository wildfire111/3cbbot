import discord
from discord.ext import commands
from discord.utils import get
import sqlite3
import asyncio
import logging
import requests
import os
from dotenv import load_dotenv

load_dotenv()
token = os.getenv('3CB_TOKEN')

intents = discord.Intents.all()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

def main():
    bot.run(token)

@bot.event
async def on_ready():
    print("Bot online")
    user = await bot.fetch_user(248740105248964608)
    await user.send("Bot online.")


if __name__ == "__main__":
    main()