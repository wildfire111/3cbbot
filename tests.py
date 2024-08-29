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
    discord_ids = [f"{i}" for i in range(10000, 99999)]
    card_names = ["CardA", "CardB", "CardC"]

    for discord_id in discord_ids:
        # Create a list of placeholder card data for each user
        cards = [f"{card}{i}" for i, card in enumerate(card_names)]
        cardstext = [f"{card} text" for card in cards]
        cardimages = [f"{card}_image_url" for card in cards]
        
        # Create an EntryCards object with placeholder data
        entry = EntryCards(user=discord_id, cards=cards, cardstext=cardstext, cardimages=cardimages, in_db=False)
        
        # Add entry to bot.entries
        bot.entries[discord_id] = entry

    print(f"Simulated {len(bot.entries)} entries with placeholder data.")
