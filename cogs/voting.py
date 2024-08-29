from discord.ext import commands
import discord
from discord import app_commands
from Battle import Battle
from datetime import datetime

class VotingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    

async def setup(bot):
    await bot.add_cog(VotingCog(bot))
