from discord.ext import commands
import discord
from discord import app_commands
import aiohttp  # Use aiohttp for async HTTP requests
from EntryCards import EntryCards

class EntriesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.entries = []  # Initialize entries attribute for the bot

    @app_commands.command(name="enter", description="Enter your three cards for your deck.")
    @app_commands.describe(card1="Card 1", card2="Card 2", card3="Card 3")
    async def enter(self, interaction: discord.Interaction, card1: str, card2: str, card3: str):
        # Defer the interaction response to avoid timeout
        await interaction.response.defer(ephemeral=True)
        if self.bot.state != 'entriesopen':
            await interaction.followup.send("Sorry, not accepting entries right now.", ephemeral=True)
        cardlist = [card1, card2, card3]
        cardnames = []
        cardstext = []
        cardsimages = []

        for card in cardlist:
            card_info = await self.scryfall_query(card)  # Await the asynchronous call
            if not card_info:
                await interaction.followup.send(f"{card} was not recognised by Scryfall, please try again.", ephemeral=True)
                print(f"card not recognised")
                return
            cardnames.append(card_info[0])
            cardstext.append(card_info[1])
            cardsimages.append(card_info[2])
        new_entry = EntryCards(interaction.user.id, cardnames, cardstext, cardsimages)
        self.bot.entries.append(new_entry)
        await interaction.followup.send("Your entry has been recorded.", ephemeral=True)
        
    async def scryfall_query(self, card):
        params = {"exact": card, "format": "json"}
        api = "https://api.scryfall.com/cards/named"

        # Use aiohttp for non-blocking requests
        async with aiohttp.ClientSession() as session:
            async with session.get(api, params=params) as response:
                if response.status != 200:
                    print(f"Error fetching card data: {response.status}")
                    return None
                
                card_data = await response.json()
                name = card_data.get("name", "Unknown")
                oracle_text = card_data.get("oracle_text", "No text available.")
                art_crop_url = card_data.get("image_uris", {}).get("art_crop", "No art URL available.")
                return [name, oracle_text, art_crop_url]

async def setup(bot):
    await bot.add_cog(EntriesCog(bot))
