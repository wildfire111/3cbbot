import asyncio
import sqlite3
import discord
from discord.ext import commands
import imagemanip
import logging

class VotingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def output_battles(self):
        """
        Prints out each battle in its own message in the channel specified by bot.channel.
        Includes the three cards from each player's corresponding EntryCards as images in the message text.
        After sending each message, stores the post ID in the corresponding Battle object.
        Once all messages are sent, updates the database with their post IDs.
        """
        channel = self.bot.channel
        if channel is None:
            logging.error("Channel not found or bot does not have access to the specified channel.")
            return

        wide_space = '\u205F' * 50
        battle_count = 0

        for battle in self.bot.battles:
            entry1 = self.bot.entries.get(battle.player1_id)
            entry2 = self.bot.entries.get(battle.player2_id)
            if entry1 and entry2:
                logging.info("Generating images")
                combined_image1 = imagemanip.combine_and_resize_images(entry1.cardsimages)
                combined_image2 = imagemanip.combine_and_resize_images(entry2.cardsimages)

                embed = discord.Embed(title=f"**Battle {battle.battle_id}:**", description="")
                embed.add_field(
                    name=f"**Player A:**",
                    value=f"\n<@{battle.player1_id}>"+"".join(f"\n*{card}*" for card in entry1.cards),
                    inline=True
                )
                embed.add_field(
                    name=f".{wide_space}**Player B:**",
                    value=f"\n.{wide_space}<@{battle.player2_id}>"+"".join(f"\n.{wide_space}*{card}*" for card in entry2.cards),
                    inline=True
                )

                battle_count += 1

                if battle_count % 3 == 0:
                    embed.add_field(
                        name="Voting Instructions",
                        value=(
                            "🅰️: Player A won both games\n"
                            "⬅️: Player A won a game and drew the other\n"
                            "🆎: Both players won a game\n"
                            "❌: Both games were a draw\n"
                            "➡️: Player B won a game and drew the other\n"
                            "🅱️: Player B won both games\n"
                            "🛑: Emergency stop. Stops scoring if you believe there's an error"
                        ),
                        inline=False
                    )

                image_bytes1 = imagemanip.image_to_bytes(combined_image1)
                image_bytes2 = imagemanip.image_to_bytes(combined_image2)
                
                discord_file1 = discord.File(fp=image_bytes1, filename="playerA.png")
                discord_file2 = discord.File(fp=image_bytes2, filename="playerB.png")

                sent_message = await channel.send(embed=embed, files=[discord_file1, discord_file2])

                battle.post_id = str(sent_message.id)
                asyncio.create_task(self.add_reactions(sent_message))

            else:
                logging.warning(f"Entries not found for players {battle.player1_id} or {battle.player2_id}.")

            await asyncio.sleep(1)

        self.update_battle_post_ids()

    def update_battle_post_ids(self):
        """
        Updates the database with the post IDs of each battle.
        """
        logging.info("Updating database with battle post IDs")
        try:
            with sqlite3.connect('3cb.db') as conn:
                cur = conn.cursor()
                for battle in self.bot.battles:
                    if battle.post_id:
                        cur.execute('''UPDATE Battles SET PostID = ? WHERE BattleID = ?''',
                                    (battle.post_id, battle.battle_id))
                        logging.info(f"Updated BattleID {battle.battle_id} with PostID {battle.post_id}.")
                conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Error updating battle post IDs in the database: {e}")

    async def add_reactions(self, message: discord.Message) -> None:
        """
        Adds reactions to a message for voting purposes.
        """
        reactions = ["🅰️", "⬅️", "🆎", "❌", "➡️", "🅱️", "🛑"]
        try:
            for reaction in reactions:
                await message.add_reaction(reaction)
        except discord.HTTPException as e:
            logging.error(f"Failed to add reactions: {e}")

    async def delete_all_posts(self):
        """Deletes all posts related to battles using their post IDs."""
        channel = self.bot.channel
        if channel is None:
            logging.error("Channel not found or bot does not have access to the specified channel.")
            return

        for battle in self.bot.battles:
            if battle.post_id:
                try:
                    message = await channel.fetch_message(battle.post_id)
                    await message.delete()
                    logging.info(f"Deleted post with ID {battle.post_id} for Battle ID {battle.battle_id}.")
                except discord.NotFound:
                    logging.warning(f"Message with ID {battle.post_id} not found. It may have already been deleted.")
                except discord.Forbidden:
                    logging.error(f"Insufficient permissions to delete message with ID {battle.post_id}.")
                except discord.HTTPException as e:
                    logging.error(f"Failed to delete message with ID {battle.post_id} due to an HTTP error: {e}")

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User):
        """
        Listens for reactions added to messages and checks if any reaction count is 3 more than the others.
        If more than one stop sign emoji is present, does nothing. Otherwise, calls resolve and clears reactions.
        """
        if user == self.bot.user:
            return

        for battle in self.bot.battles:
            if reaction.message.id == battle.post_id:
                reactions = reaction.message.reactions
                stop_sign_count = sum(1 for r in reactions if str(r.emoji) == "🛑")
                
                if stop_sign_count > 1:
                    return

                counts = [r.count for r in reactions]
                for count in counts:
                    if any(count >= other_count + 3 for other_count in counts if count != other_count):
                        emoji_str = str(reaction.emoji) if isinstance(reaction.emoji, str) else reaction.emoji.name
                        await self.resolve(emoji_str, battle)
                        try:
                            await reaction.message.clear_reactions()
                            logging.info(f"Cleared reactions from message {reaction.message.id}.")
                        except discord.HTTPException as e:
                            logging.error(f"Failed to clear reactions: {e}")
                        break
    async def resolve(self, emoji: str, battle) -> None:
        """
        Resolves the battle outcome based on the emoji selected and updates the player scores.
        
        Scoring Rules:
        - 🅰️: Player A won both games -> Player 1: 6 points, Player 2: 0 points
        - ⬅️: Player A won a game and drew the other -> Player 1: 4 points, Player 2: 1 point
        - 🆎: Both players won a game -> Player 1: 3 points, Player 2: 3 points
        - ❌: Both games were a draw -> Player 1: 2 points, Player 2: 2 points
        - ➡️: Player B won a game and drew the other -> Player 1: 1 point, Player 2: 4 points
        - 🅱️: Player B won both games -> Player 1: 0 points, Player 2: 6 points
        """
        score_map = {
            "🅰️": (6, 0),
            "⬅️": (4, 1),
            "🆎": (3, 3),
            "❌": (2, 2),
            "➡️": (1, 4),
            "🅱️": (0, 6)
        }

        if emoji in score_map:
            battle.points_player1, battle.points_player2 = score_map[emoji]
            battle.resolved = True
        else:
            logging.warning(f"Invalid emoji: {emoji}")
            return

        try:
            with sqlite3.connect('3cb.db') as conn:
                cur = conn.cursor()
                cur.execute('''UPDATE Battles SET PointsPlayer1 = ?, PointsPlayer2 = ?, Resolved = ? WHERE BattleID = ?''',
                            (battle.points_player1, battle.points_player2, int(battle.resolved), battle.battle_id))
                conn.commit()
                logging.info(f"Resolved BattleID {battle.battle_id}: Player 1 - {battle.points_player1}, Player 2 - {battle.points_player2}.")
        except sqlite3.Error as e:
            logging.error(f"Error updating battle scores in the database: {e}")

    async def calculate_standings(self) -> None:
        """
        Totals up the points for each player, displays their standings in order,
        and updates the existing table in the database by accumulating points.
        Checks that all battles are resolved before proceeding.
        """
        unresolved_battles = [battle for battle in self.bot.battles if not battle.resolved]
        
        if unresolved_battles:
            logging.warning("Unresolved battles found:")
            for battle in unresolved_battles:
                entry1 = self.bot.entries.get(battle.player1_id)
                entry2 = self.bot.entries.get(battle.player2_id)
                entry1_details = f"Player 1: <@{battle.player1_id}>, Cards: {', '.join(entry1.cards)}" if entry1 else "Player 1: Not found"
                entry2_details = f"Player 2: <@{battle.player2_id}>, Cards: {', '.join(entry2.cards)}" if entry2 else "Player 2: Not found"
                logging.warning(f"Battle ID: {battle.battle_id}, {entry1_details}, {entry2_details}")
            return

        player_points = {}

        for battle in self.bot.battles:
            player_points[battle.player1_id] = player_points.get(battle.player1_id, 0) + battle.points_player1
            player_points[battle.player2_id] = player_points.get(battle.player2_id, 0) + battle.points_player2

        try:
            with sqlite3.connect('3cb.db') as conn:
                cur = conn.cursor()
                cur.execute('SELECT PlayerID, Points FROM Standings')
                existing_standings = cur.fetchall()

                for player_id, existing_points in existing_standings:
                    player_points[player_id] = player_points.get(player_id, 0) + existing_points

        except sqlite3.Error as e:
            logging.error(f"Error fetching existing standings from the database: {e}")

        sorted_standings = sorted(player_points.items(), key=lambda x: x[1], reverse=True)

        embed = discord.Embed(title="Player Standings", description="Here are the current standings based on battle results.", color=discord.Color.blue())

        for rank, (player_id, points) in enumerate(sorted_standings, start=1):
            embed.add_field(name=f"{rank}. <@{player_id}>", value=f"{points} points", inline=False)

        channel = self.bot.get_channel(self.bot.channel.id)  # Changed to access channel ID
        if channel:
            await channel.send(embed=embed)
        else:
            logging.error("Channel not found or bot does not have access to the specified channel.")

        try:
            with sqlite3.connect('3cb.db') as conn:
                cur = conn.cursor()
                for player_id, points in player_points.items():
                    cur.execute('INSERT INTO Standings (PlayerID, Points) VALUES (?, ?) ON CONFLICT(PlayerID) DO UPDATE SET Points = ?', (player_id, points, points))
                conn.commit()
                logging.info("Standings have been updated in the database.")
        except sqlite3.Error as e:
            logging.error(f"Error updating standings in the database: {e}")

async def setup(bot):
    """Setup function to add the cog to the bot."""
    await bot.add_cog(VotingCog(bot))
