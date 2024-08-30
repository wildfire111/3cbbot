import asyncio
import sqlite3
import discord
from discord.ext import commands
import imagemanip

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
        # Fetch the channel from bot.channel
        channel = self.bot.channel
        if channel is None:
            print("Channel not found or bot does not have access to the specified channel.")
            return
        
        # Medium Mathematical Space character for padding
        wide_space = '\u205F' * 50

        battle_count = 0
        
        # Iterate over each battle in bot.battles
        for battle in self.bot.battles:
            # Retrieve EntryCards for each player
            entry1 = self.bot.entries.get(battle.player1_id)
            entry2 = self.bot.entries.get(battle.player2_id)
            if entry1 and entry2:
                print("Generating images")
                # Combine card images for Player A using the function from imagemanip.py
                combined_image1 = imagemanip.combine_and_resize_images(entry1.cardsimages)
                # Combine card images for Player B using the function from imagemanip.py
                combined_image2 = imagemanip.combine_and_resize_images(entry2.cardsimages)

                # Create a Discord embed message with the battle ID and player details
                embed = discord.Embed(title=f"**Battle {battle.battle_id}:**", description="")  # Bold title

                embed.add_field(
                    name=f"**Player A: <@{battle.player1_id}>**",  # Changed to Player A
                    value="\n".join(f"*{card}*" for card in entry1.cards),  # Italicize cards for Player A
                    inline=True
                )
                embed.add_field(
                    name=f".{wide_space}**Player B: <@{battle.player2_id}>**",  # Changed to Player B
                    value="\n".join(f".{wide_space}*{card}*" for card in entry2.cards),  # Adds wide spaces before each card for Player B
                    inline=True
                )

                # Increment battle count
                battle_count += 1

                # Check if this is every third battle to add voting instructions
                if battle_count % 3 == 0:
                    # Add a field for voting instructions
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
                
                # Convert images to bytes
                image_bytes1 = imagemanip.image_to_bytes(combined_image1)
                image_bytes2 = imagemanip.image_to_bytes(combined_image2)
                
                # Create discord files from image bytes
                discord_file1 = discord.File(fp=image_bytes1, filename="playerA.png")
                discord_file2 = discord.File(fp=image_bytes2, filename="playerB.png")
                discord_file3 = discord.File(fp=image_bytes1, filename="playerA.png")

                # Send message with files
                sent_message = await channel.send(embed=embed, files=[discord_file1, discord_file2, discord_file3])

                # Store the post ID in the Battle object
                battle.post_id = str(sent_message.id)

                # Add reactions asynchronously
                asyncio.create_task(self.add_reactions(sent_message))

            else:
                print(f"Entries not found for players {battle.player1_id} or {battle.player2_id}.")

            # Add a delay to avoid hitting rate limits
            await asyncio.sleep(1)  # Adjust the delay as needed

        # After sending all messages, update the database with their post IDs
        self.update_battle_post_ids()

    def update_battle_post_ids(self):
        """
        Updates the database with the post IDs of each battle.
        """
        print("updating db with battle post id")
        try:
            with sqlite3.connect('3cb.db') as conn:
                cur = conn.cursor()
                for battle in self.bot.battles:
                    if battle.post_id:  # Only update if post_id is set
                        # Use an UPDATE statement to overwrite the PostID in the database
                        cur.execute('''UPDATE Battles SET PostID = ? WHERE BattleID = ?''',
                                    (battle.post_id, battle.battle_id))
                        print(f"Updated BattleID {battle.battle_id} with PostID {battle.post_id}.")
                conn.commit()
        except sqlite3.Error as e:
            print(f"Error updating battle post IDs in the database: {e}")
    
    async def add_reactions(self, message):
        """
        Adds reactions to a message for voting purposes.
        """
        try:
            # Add reactions for voting
            await message.add_reaction("🅰️")  # Reaction for Player A
            await message.add_reaction("⬅️")  # Reaction for left arrow
            await message.add_reaction("🆎")  # Reaction for AB symbol
            await message.add_reaction("❌")  # Reaction for cross
            await message.add_reaction("➡️")  # Reaction for right arrow
            await message.add_reaction("🅱️")  # Reaction for Player B
            await message.add_reaction("🛑")  # Stop symbol reaction
        except discord.HTTPException as e:
            print(f"Failed to add reactions: {e}")

    async def delete_all_posts(self):
    
        # Fetch the channel from bot.channel
        channel = self.bot.channel
        if channel is None:
            print("Channel not found or bot does not have access to the specified channel.")
            return
        
        # Iterate over each battle in bot.battles
        for battle in self.bot.battles:
            print(battle)
            print(battle.post_id)
            if battle.post_id:  # Ensure there is a post_id to delete
                try:
                    # Fetch the message using post_id
                    message = await channel.fetch_message(battle.post_id)
                    print(message)
                    # Delete the message
                    await message.delete()
                    print(f"Deleted post with ID {battle.post_id} for Battle ID {battle.battle_id}.")
                except discord.NotFound:
                    print(f"Message with ID {battle.post_id} not found. It may have already been deleted.")
                except discord.Forbidden:
                    print(f"Insufficient permissions to delete message with ID {battle.post_id}.")
                except discord.HTTPException as e:
                    print(f"Failed to delete message with ID {battle.post_id} due to an HTTP error: {e}")

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """
        Listens for reactions added to messages and checks if any reaction count is 3 more than the others.
        If more than one stop sign emoji is present, does nothing. Otherwise, calls score and clears reactions.
        """
        # Ensure the bot doesn't respond to its own reactions
        if user == self.bot.user:
            return
        
        # Check if the reaction is on a message that belongs to a battle
        for battle in self.bot.battles:
            if reaction.message.id == battle.post_id:
                # Get all reactions on the message
                reactions = reaction.message.reactions

                # Count the number of stop sign emojis
                stop_sign_count = sum(1 for r in reactions if str(r.emoji) == "🛑")
                
                # Do nothing if there is more than one stop sign emoji
                if stop_sign_count > 1:
                    return

                # Find the reaction count that is 3 more than any other
                counts = [r.count for r in reactions]
                for count in counts:
                    if any(count >= other_count + 3 for other_count in counts if count != other_count):
                        # Call the score function with the reaction emoji and battle object
                        emoji_str = str(reaction.emoji) if isinstance(reaction.emoji, str) else reaction.emoji.name
                        await self.resolve(emoji_str, battle)

                        # Clear all reactions from the post
                        try:
                            await reaction.message.clear_reactions()
                            print(f"Cleared reactions from message {reaction.message.id}.")
                        except discord.HTTPException as e:
                            print(f"Failed to clear reactions: {e}")
                        break

    async def resolve(self, emoji, battle):
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
        if emoji == "🅰️":
            # Player A won both games
            battle.points_player1 = 6
            battle.points_player2 = 0
        elif emoji == "⬅️":
            # Player A won a game and drew the other
            battle.points_player1 = 4
            battle.points_player2 = 1
        elif emoji == "🆎":
            # Both players won a game
            battle.points_player1 = 3
            battle.points_player2 = 3
        elif emoji == "❌":
            # Both games were a draw
            battle.points_player1 = 2
            battle.points_player2 = 2
        elif emoji == "➡️":
            # Player B won a game and drew the other
            battle.points_player1 = 1
            battle.points_player2 = 4
        elif emoji == "🅱️":
            # Player B won both games
            battle.points_player1 = 0
            battle.points_player2 = 6
        else:
            # Invalid emoji, do nothing
            return

        # Update the battle in the database with the resolved scores
        try:
            with sqlite3.connect('3cb.db') as conn:
                cur = conn.cursor()
                cur.execute('''UPDATE Battles SET PointsPlayer1 = ?, PointsPlayer2 = ?, Resolved = ? WHERE BattleID = ?''',
                            (battle.points_player1, battle.points_player2, 1, battle.battle_id))
                conn.commit()
                print(f"Resolved BattleID {battle.battle_id}: Player 1 - {battle.points_player1}, Player 2 - {battle.points_player2}.")
        except sqlite3.Error as e:
            print(f"Error updating battle scores in the database: {e}")

    async def calculate_standings(self):
        """
        Totals up the points for each player, displays their standings in order,
        and updates the existing table in the database by accumulating points.
        Checks that all battles are resolved before proceeding.
        """
        # Check if all battles are resolved
        unresolved_battles = []
        for battle in self.bot.battles:
            if not battle.resolved:
                unresolved_battles.append(battle)
        
        # If there are unresolved battles, print them and return
        if unresolved_battles:
            print("Unresolved battles found:")
            for battle in unresolved_battles:
                entry1 = self.bot.entries.get(battle.player1_id)
                entry2 = self.bot.entries.get(battle.player2_id)
                entry1_details = f"Player 1: <@{battle.player1_id}>, Cards: {', '.join(entry1.cards)}" if entry1 else "Player 1: Not found"
                entry2_details = f"Player 2: <@{battle.player2_id}>, Cards: {', '.join(entry2.cards)}" if entry2 else "Player 2: Not found"
                print(f"Battle ID: {battle.battle_id}, {entry1_details}, {entry2_details}")
            return

        # Dictionary to store total points for each player
        player_points = {}

        # Calculate total points for each player from all battles
        for battle in self.bot.battles:
            player1_id = battle.player1_id
            player2_id = battle.player2_id
            
            # Add points for player 1
            player_points[player1_id] = player_points.get(player1_id, 0) + battle.points_player1
            
            # Add points for player 2
            player_points[player2_id] = player_points.get(player2_id, 0) + battle.points_player2

        # Retrieve existing points from the Standings table and accumulate them
        try:
            with sqlite3.connect('3cb.db') as conn:
                cur = conn.cursor()

                # Fetch existing points
                cur.execute('SELECT PlayerID, Points FROM Standings')
                existing_standings = cur.fetchall()

                # Update player_points with existing points
                for player_id, existing_points in existing_standings:
                    player_points[player_id] = player_points.get(player_id, 0) + existing_points

        except sqlite3.Error as e:
            print(f"Error fetching existing standings from the database: {e}")

        # Sort players by total points in descending order
        sorted_standings = sorted(player_points.items(), key=lambda x: x[1], reverse=True)

        # Create an embed to display the standings
        embed = discord.Embed(title="Player Standings", description="Here are the current standings based on battle results.", color=discord.Color.blue())

        # Add fields to the embed for each player and their points
        for rank, (player_id, points) in enumerate(sorted_standings, start=1):
            embed.add_field(name=f"{rank}. <@{player_id}>", value=f"{points} points", inline=False)

        # Send the embed to the specified channel
        channel = self.bot.get_channel(self.bot.channel)
        if channel is not None:
            await channel.send(embed=embed)
        else:
            print("Channel not found or bot does not have access to the specified channel.")

        # Update standings in the existing table in the database
        try:
            with sqlite3.connect('3cb.db') as conn:
                cur = conn.cursor()

                # Update the Standings table with the accumulated points
                for player_id, points in player_points.items():
                    cur.execute('INSERT INTO Standings (PlayerID, Points) VALUES (?, ?) ON CONFLICT(PlayerID) DO UPDATE SET Points = ?', (player_id, points, points))
                conn.commit()
                print("Standings have been updated in the database.")
        except sqlite3.Error as e:
            print(f"Error updating standings in the database: {e}")


async def setup(bot):
    await bot.add_cog(VotingCog(bot))
