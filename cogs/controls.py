from discord.ext import commands
import utils
import sqlite3

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
        if message.content.startswith('!getstate'):
            await self.get_state(message)
        if message.content.startswith('!setstate'):
            new_state = message.content[len('!setstate '):].strip()
            if len(new_state) == 0:
                await message.channel.send(f"Please enter a state")
            else:
                await utils.set_state(new_state)
        if message.content.startswith('!newround'):
            await self.new_round()
        elif message.content.startswith('!channel'):
            await self.set_channel(message)

    async def get_state(self, message):
        await message.channel.send(f"Bot state: {self.bot.state}")

    async def new_round(self):
        try:
            with sqlite3.connect('3cb.db') as conn:
                cur = conn.cursor()
                cur.execute("UPDATE Timeline SET CurRound = CurRound + 1")
                conn.commit()
                print("Database round number incremented.")
        except Exception as e:
            print(f"Error updating round number in database: {e}")
            return
        self.bot.round += 1
        print(f"Starting round {self.bot.round}")
        self.bot.entries.clear()
        print("Cleared entries")
        utils.set_state('entriesopen')
        print(f"Bot status: {self.bot.state}")

    async def set_channel(self, message):
        try:
            channel_id = int(message.content[len('!channel '):].strip())
        except ValueError:
            await message.channel.send("Invalid channel ID. Please provide a valid numeric channel ID.")
            return

        channel = self.bot.get_channel(channel_id)
        if channel is None:
            await message.channel.send("Invalid channel ID. Please provide a valid channel ID.")
            return

        self.bot.channel = channel

        # Store the channel ID in the database
        try:
            with sqlite3.connect('3cb.db') as conn:
                cur = conn.cursor()
                cur.execute('''UPDATE Timeline SET Channel = ?''', (channel_id,))
                conn.commit()
            print(f"Channel set to {channel.mention} for the competition.")
        except Exception as e:
            print("An error occurred while setting the channel.")


async def setup(bot):
    await bot.add_cog(ControlCog(bot))