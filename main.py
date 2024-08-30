import os
import asyncio
import logging
import sqlite3
from dotenv import load_dotenv
import requests
import discord
from discord.ext import commands
from discord.utils import get
import utils

# Load environment variables
load_dotenv()
token = os.getenv('BOT_KEY')
admin_id = os.getenv('ADMIN_ID')

# Configure logging to print to console with timestamps
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Configure bot intents
intents = discord.Intents.all()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='&', intents=intents)
bot.state = 'startup'
bot.admin = admin_id

# Constants
COGS = ['cogs.entries', 'cogs.controls', 'cogs.voting']

async def main():
    logging.info("Bot starting")
    for cog in COGS:
        try:
            await bot.load_extension(cog)
            logging.info(f"Loaded {cog}")
        except Exception as e:
            logging.error(f"Failed to load {cog}: {e}")
    
    utils.initialise_db()
    await bot.start(token)

@bot.event
async def on_ready():
    bot.state = 'startup'
    logging.info("Synching commands")
    
    try:
        await bot.tree.sync()
    except Exception as e:
        logging.error(f"Sync error: {e}")

    bot.battles = []
    bot.entries = {}
    
    logging.info("Loading from DB")
    utils.load_entries_from_db(bot)
    
    logging.info("Loading state")
    utils.load_timeline_values(bot)
    
    logging.info("Starting archivist")
    asyncio.create_task(utils.archivist(bot))
    
    logging.info("Startup complete")

if __name__ == "__main__":
    asyncio.run(main())
