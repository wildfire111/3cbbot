from discord.ext import commands
import discord
from discord import app_commands
import requests
import EntryCards

class EntriesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        #self.bot.tree.add_command(self.enter)

    @app_commands.command(name="enter", description="Enter your three cards for your deck.")
    @app_commands.describe(card1="Card 1", card2="Card 2", card3="Card 3")
    async def enter(self, interaction: discord.Interaction, card1: str, card2: str, card3: str):
        response = f"Received strings:\n1: {card1}\n2: {card2}\n3: {card3}"
        await interaction.response.send_message(response,ephemeral=True)
        cardlist = [card1,card2,card3]
        carddata = []
        for card in cardlist:
            card_info = scryfall_query(card)
            if not card_info:
                await interaction.response.send_message(f"{card} was not recognised by Scryfall, please try again.")
                return
            carddata.append(card_info)
        new_entry = EntryCards()
        
    async def scryfall_query(card):
        params = {"exact":card,"format":"json"}
        api = "https://api.scryfall.com/cards/named"
        response = requests.get(api,params=params)
        if not response.ok:
            return False
        else:
            card_data = response.json()
            name = card_data.get("name","Unknown")
            oracle_text = card_data.get("oracle_text", "No text available.")
            art_crop_url = card_data.get("image_uris", {}).get("art_crop", "No art URL available.")
            return [name,oracle_text,art_crop_url]

            


async def setup(bot):
    await bot.add_cog(EntriesCog(bot))
