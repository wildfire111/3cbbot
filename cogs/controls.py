from discord.ext import commands
import utils
import sqlite3
import pairing
import testinput

class ControlCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        # Ensure the bot does not reply to itself
        if message.author == self.bot.user:
            return
        
        #only listen to me
        if message.author.id != self.bot.admin or message.content[0] != "!":
            return
        
        if message.content.startswith('!getstate'):
            await self.get_state(message)

        elif message.content.startswith('!setstate'):
            new_state = message.content[len('!setstate '):].strip()
            if len(new_state) == 0:
                await message.channel.send(f"Please enter a state")
            else:
                await utils.set_state(self.bot,new_state)
        elif message.content.startswith('!newround'):
            await self.new_round()

        elif message.content.startswith('!pair'):
            await utils.set_state(self.bot,'pairing')
            await self.pairings()

        elif message.content.startswith('!vote'):
            voting_cog = self.bot.get_cog('VotingCog')
            print(f"Outputting {len(self.bot.battles)} battles in {self.bot.channel}")
            await voting_cog.output_battles()

        elif message.content.startswith('!deleteposts'):
            voting_cog = self.bot.get_cog('VotingCog')
            print(f"Deleting battles in {self.bot.channel}")
            await voting_cog.delete_all_posts()
            

        elif message.content.startswith('!fakeentries'):
            print("faking entries")
            testinput.simulate_entries(self.bot)

        elif message.content.startswith('!channel'):
            await self.set_channel(message)

        elif message.content.startswith('!manualscore'):
            await self.manual_score(message)

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
    
    async def manual_score(self, message):
        """
        Manually resolves a battle using the given emoji and battle ID.
        
        Usage: !manualscore {emoji} {battleid}
        """
        parts = message.content.split()
        if len(parts) != 3:
            await message.channel.send("Usage: !manualscore {emoji} {battleid}")
            return

        emoji = parts[1]
        try:
            battle_id = int(parts[2])
        except ValueError:
            await message.channel.send("Invalid battle ID. Please enter a valid number.")
            return

        # Find the battle with the given battle_id
        battle = next((b for b in self.bot.battles if str(b.battle_id) == str(battle_id)), None)
        
        if not battle:
            await message.channel.send(f"Battle with ID {battle_id} not found.")
            return

        # Check if the emoji is valid
        valid_emojis = ["🅰️", "⬅️", "🆎", "❌", "➡️", "🅱️"]
        if emoji not in valid_emojis:
            await message.channel.send("Invalid emoji. Please use a valid emoji to score the battle.")
            return

        # Resolve the battle using the VotingCog's resolve method
        voting_cog = self.bot.get_cog("VotingCog")
        if voting_cog:
            await voting_cog.resolve(emoji, battle)
            print("flag1")
            message_to_clear = await self.bot.channel.fetch_message(battle.post_id)
            print("flag3")
            await message_to_clear.clear_reactions()
            print(f"Battle {battle_id} resolved and reactions cleared.")
        else:
            print("Error: no voting cog.")


async def setup(bot):
    await bot.add_cog(ControlCog(bot))