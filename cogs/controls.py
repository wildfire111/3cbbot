from discord.ext import commands
import utils
import sqlite3
import pairing
import tests

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
                await utils.set_state(self.bot,new_state)
        if message.content.startswith('!newround'):
            await self.new_round()

        if message.content.startswith('!pair'):
            await utils.set_state(self.bot,'pairing')
            await self.pairings()

        if message.content.startswith('!vote'):
            voting_cog = self.bot.get_cog('VotingCog')
            print(f"Outputting {len(self.bot.battles)} battles in {self.bot.channel}")
            await voting_cog.output_battles()

        if message.content.startswith('!deleteposts'):
            voting_cog = self.bot.get_cog('VotingCog')
            print(f"Deleting battles in {self.bot.channel}")
            await voting_cog.delete_all_posts()
            

        if message.content.startswith('!fakeentries'):
            print("faking entries")
            tests.simulate_entries(self.bot)

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
            self.bot.round += 1
            print(f"Starting round {self.bot.round}")
            self.bot.entries.clear()
            print("Cleared entries")
            await utils.set_state(self.bot,'entriesopen')
            print(f"Bot status: {self.bot.state}")
        except Exception as e:
            print(f"Error updating round number: {e}")
            return
        

    async def pairings(self):
        """
        Generates all possible pairings using generate_pairings and enters them into the database.
        Overwrites the bot.battles with the new pairings.
        """
        # Generate pairings (Battle objects)
        battles = pairing.generate_pairings(self.bot)
        
        try:
            # Open a database connection
            with sqlite3.connect('3cb.db') as conn:
                cur = conn.cursor()
                cur.execute('DELETE FROM Battles;')
                # Loop through each battle and insert into the database
                for battle in battles:
                    # Insert the battle into the Battles table
                    cur.execute('''INSERT INTO Battles (BattleID,Player1ID, Player2ID, Resolved, PointsPlayer1, PointsPlayer2)
                                VALUES (?, ?, ?, ?, ?, ?)''',
                                (battle.battle_id,battle.player1_id, battle.player2_id, int(battle.resolved), 
                                battle.points_player1, battle.points_player2))
                
                # Commit the changes to the database
                conn.commit()
                print(f"Inserted {len(battles)} pairings into the database.")
            
            # Overwrite bot.battles with the new battles
            self.bot.battles = battles
            print(f"Bot battles have been updated with {len(self.bot.battles)} new battles.")
            await utils.set_state(self.bot,'paired')
        except Exception as e:
            print(f"Error inserting pairings into the database: {e}")
        

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
        await channel.send("Channel set")


async def setup(bot):
    await bot.add_cog(ControlCog(bot))