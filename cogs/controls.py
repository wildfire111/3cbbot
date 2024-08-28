from discord.ext import commands
import utils

class ControlCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        # Ensure the bot does not reply to itself
        if message.author == self.bot.user:
            return
        #only listen to me
        if message.author.id != 248740105248964608 or message.content[0] != "!":
            return
        await message.channel.send(message.content)
        # content = message.content.lower()
        # if content.startswith('!help'):
        #     await message.channel.send(utils.help())
        # elif content.startswith('!rules'):
        #     await message.channel.send(utils.rules())
        # # elif self.bot.state == 'entriesopen':
        # #     await self.receive_entry(message)
        # # else:
        # #     await message.channel.send("Sorry, entries are closed right now.")
        # else:
        #     await message.channel.send("Please use !help or !rules")
        
    async def receive_entry(self, message):
        pass


async def setup(bot):
    await bot.add_cog(ControlCog(bot))