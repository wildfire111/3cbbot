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
                            "🅱️: Player B won both games"
                        ),
                        inline=False
                    )
                
                # Convert images to bytes
                image_bytes1 = imagemanip.image_to_bytes(combined_image1)
                image_bytes2 = imagemanip.image_to_bytes(combined_image2)
                
                # Create discord files from image bytes
                discord_file1 = discord.File(fp=image_bytes1, filename="playerA.png")
                discord_file2 = discord.File(fp=image_bytes2, filename="playerB.png")

                # Send message with files
                sent_message = await channel.send(embed=embed, files=[discord_file1, discord_file2])

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

async def setup(bot):
    await bot.add_cog(VotingCog(bot))
