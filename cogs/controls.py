from discord.ext import commands
import utils
import sqlite3
import pairing
import testinput
import logging

class ControlCog(commands.Cog):
    """Cog for controlling various bot operations."""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        """
        Listens for messages and processes commands sent by the bot admin.

        Args:
            message (discord.Message): The message object from Discord.
        """
        # Ensure the bot does not reply to itself
        if message.author == self.bot.user:
            return

        # Only listen to messages from the admin with a "!" prefix
        if str(message.author.id) != str(self.bot.admin) or not message.content.startswith("!"):
            return
        # Process commands based on message content
        command_map = {
            '!getstate': self.get_state,
            '!setstate': self.set_state,
            '!newround': self.new_round,
            '!pair': self.pairings,
            '!vote': self.output_battles,
            '!deleteposts': self.delete_all_posts,
            '!fakeentries': self.fake_entries,
            '!channel': self.set_channel,
            '!manualscore': self.manual_score,
        }

        # Extract the command and execute the corresponding method
        command = message.content.split(' ')[0]
        if command in command_map:
            await command_map[command](message)

    async def get_state(self, message):
        """Sends the current state of the bot."""
        await message.channel.send(f"Bot state: {self.bot.state}")

    async def set_state(self, message):
        """Sets a new state for the bot."""
        new_state = message.content[len('!setstate '):].strip()
        if not new_state:
            await message.channel.send("Please enter a state")
        else:
            await utils.set_state(self.bot, new_state)

    async def new_round(self, message):
        """Prepares for a new round by incrementing the round number and clearing entries."""
        try:
            with sqlite3.connect('3cb.db') as conn:
                cur = conn.cursor()
                cur.execute("UPDATE Timeline SET CurRound = CurRound + 1")
                conn.commit()
                logging.info("Database round number incremented.")
            self.bot.round += 1
            logging.info(f"Starting round {self.bot.round}")
            self.bot.entries.clear()
            logging.info("Cleared entries")
            await utils.set_state(self.bot, 'entriesopen')
            logging.info(f"Bot status: {self.bot.state}")
        except Exception as e:
            logging.error(f"Error updating round number: {e}")

    async def pairings(self, message):
        """
        Generates all possible pairings using generate_pairings and enters them into the database.
        Overwrites the bot.battles with the new pairings.
        """
        battles = pairing.generate_pairings(self.bot)

        try:
            with sqlite3.connect('3cb.db') as conn:
                cur = conn.cursor()
                cur.execute('DELETE FROM Battles;')
                for battle in battles:
                    cur.execute(
                        '''INSERT INTO Battles (BattleID,Player1ID, Player2ID, Resolved, PointsPlayer1, PointsPlayer2)
                        VALUES (?, ?, ?, ?, ?, ?)''',
                        (battle.battle_id, battle.player1_id, battle.player2_id, int(battle.resolved),
                         battle.points_player1, battle.points_player2)
                    )
                conn.commit()
                logging.info(f"Inserted {len(battles)} pairings into the database.")
            
            self.bot.battles = battles
            logging.info(f"Bot battles have been updated with {len(self.bot.battles)} new battles.")
            await utils.set_state(self.bot, 'paired')
        except Exception as e:
            logging.error(f"Error inserting pairings into the database: {e}")

    async def set_channel(self, message):
        """Sets the bot's operating channel."""
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

        battle = next((b for b in self.bot.battles if str(b.battle_id) == str(battle_id)), None)
        
        if not battle:
            await message.channel.send(f"Battle with ID {battle_id} not found.")
            return

        valid_emojis = ["🅰️", "⬅️", "🆎", "❌", "➡️", "🅱️"]
        if emoji not in valid_emojis:
            await message.channel.send("Invalid emoji. Please use a valid emoji to score the battle.")
            return

        voting_cog = self.bot.get_cog("VotingCog")
        if voting_cog:
            await voting_cog.resolve(emoji, battle)
            logging.info(f"Battle {battle_id} resolved.")
            message_to_clear = await self.bot.channel.fetch_message(battle.post_id)
            await message_to_clear.clear_reactions()
            logging.info(f"Reactions cleared for battle {battle_id}.")
        else:
            logging.error("Error: no voting cog.")

    async def output_battles(self, message):
        """Outputs battles using the VotingCog."""
        voting_cog = self.bot.get_cog('VotingCog')
        if voting_cog:
            logging.info(f"Outputting {len(self.bot.battles)} battles in {self.bot.channel}")
            await voting_cog.output_battles()
        else:
            logging.error("Error: VotingCog not found.")

    async def delete_all_posts(self, message):
        """Deletes all posts related to battles using the VotingCog."""
        voting_cog = self.bot.get_cog('VotingCog')
        if voting_cog:
            logging.info(f"Deleting battles in {self.bot.channel}")
            await voting_cog.delete_all_posts()
        else:
            logging.error("Error: VotingCog not found.")

    async def fake_entries(self, message):
        """Simulates fake entries for testing purposes."""
        logging.info("Faking entries")
        testinput.simulate_entries(self.bot)


async def setup(bot):
    """Setup function to add the cog to the bot."""
    await bot.add_cog(ControlCog(bot))
