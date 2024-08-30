import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import logging
from EntryCards import EntryCards
from datetime import datetime

# Constants
API_URL = "https://api.scryfall.com/cards/named"

class EntriesCog(commands.Cog):
    """Cog for handling deck entries."""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="enter", description="Enter your three cards for your deck.")
    @app_commands.describe(card1="Card 1", card2="Card 2", card3="Card 3")
    async def enter(self, interaction: discord.Interaction, card1: str, card2: str, card3: str):
        """Command to enter three cards for a deck."""
        await interaction.response.defer(ephemeral=True)

        # Check if entries are open
        if self.bot.state != 'entriesopen':
            await interaction.followup.send("Sorry, not accepting entries right now.", ephemeral=True)
            return
        
        cardlist = [card1, card2, card3]
        cardnames, cardstext, cardsimages = [], [], []

        for card in cardlist:
            card_info = await self.scryfall_query(card)
            if not card_info:
                await interaction.followup.send(f"{card} was not recognised by Scryfall, please try again.", ephemeral=True)
                return
            cardnames.append(card_info[0])
            cardstext.append(card_info[1])
            cardsimages.append(card_info[2])
        
        new_entry = EntryCards(interaction.user.id, cardnames, cardstext, cardsimages)
        self.bot.entries[str(interaction.user.id)] = new_entry
        
        await interaction.followup.send("Your entry has been recorded.", ephemeral=True)
        logging.info(f"Entry recorded: {interaction.user.name} at {datetime.now()}")

    @app_commands.command(name="get-entry", description="Retrieve your current entry.")
    async def getentry(self, interaction: discord.Interaction):
        """Command to get the user's current entry."""
        user_id = str(interaction.user.id)
        if user_id in self.bot.entries:
            entry = self.bot.entries[user_id]
            entry_details = f"Your current entry cards: {', '.join(entry.cards)}"
            await interaction.response.send_message(entry_details, ephemeral=True)
        else:
            await interaction.response.send_message("You do not have an entry recorded.", ephemeral=True)

    async def scryfall_query(self, card):
        """Query the Scryfall API for card information."""
        params = {"exact": card, "format": "json"}

        async with aiohttp.ClientSession() as session:
            async with session.get(API_URL, params=params) as response:
                if response.status != 200:
                    logging.error(f"Error fetching card data: {response.status}")
                    return None
                
                card_data = await response.json()
                name = card_data.get("name", "Unknown")
                oracle_text = card_data.get("oracle_text", "No text available.")
                art_crop_url = card_data.get("image_uris", {}).get("art_crop", "No art URL available.")
                return [name, oracle_text, art_crop_url]

async def setup(bot):
    """Setup function to add the cog to the bot."""
    await bot.add_cog(EntriesCog(bot))
