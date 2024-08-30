from EntryCards import EntryCards

def simulate_entries(bot):
    """
    Simulates 10 entries with placeholder card names and Discord IDs for testing.
    
    Args:
        bot: The bot instance to which entries will be added.
    """
    # Clear existing entries
    bot.entries.clear()

    # Placeholder Discord IDs and card data
    discord_ids = [f"{i}" for i in range(90,94)]
    card_names = ["Black Lotus", "Swords to Plowshares", "Colossal Dreadmaw"]
    print("generated fake data")
    for discord_id in discord_ids:
        # Create a list of placeholder card data for each user
        cards = [f"{card}{i}" for i, card in enumerate(card_names)]
        cardstext = [f"{card} text" for card in cards]
        cardsimages = [f"https://cards.scryfall.io/art_crop/front/b/d/bd8fa327-dd41-4737-8f19-2cf5eb1f7cdd.jpg?1614638838",
                       "https://cards.scryfall.io/art_crop/front/b/d/bd8fa327-dd41-4737-8f19-2cf5eb1f7cdd.jpg?1614638838",
                       "https://cards.scryfall.io/art_crop/front/e/4/e49de6f8-f837-4cef-96ff-a48448b453a1.jpg?1723227288"]
        
        # Create an EntryCards object with placeholder data
        entry = EntryCards(user=discord_id, cards=cards, cardstext=cardstext, cardsimages=cardsimages, in_db=False)
        
        # Add entry to bot.entries
        bot.entries[discord_id] = entry

    print(f"Simulated {len(bot.entries)} entries with placeholder data.")
