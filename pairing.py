from Battle import Battle

def generate_pairings(bot):
    """
    Generates a list of battles where each player plays against every other player.
    The battles are instances of the Battle class created using Discord IDs from bot.entries.
    
    Args:
        bot: The bot instance containing the entries dictionary with Discord IDs as keys.
    
    Returns:
        A list of Battle objects, each representing a pairing (player1 vs player2).
    """
    # Get the list of Discord IDs from bot.entries keys
    discord_ids = list(bot.entries.keys())
    
    # Initialize an empty list to store the battles
    battles = []

    # Loop through each Discord ID to create battles
    for i in range(len(discord_ids)):
        for j in range(i + 1, len(discord_ids)):
            # Create a Battle object with the two players and add it to the battles list
            battle = Battle(player1_id=discord_ids[i], player2_id=discord_ids[j])
            battles.append(battle)
    
    return battles