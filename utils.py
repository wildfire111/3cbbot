#util.py
#different bits and bobs to make it all run

import sqlite3
from EntryCards import EntryCards
import asyncio

def initialise_db():
    """
    Checks the database and creates tables if they do not exist.
    """
    # SQL commands to create necessary tables
    tables_to_create = [
        ('Points', '''CREATE TABLE "Points" (
                        "Card" TEXT, 
                        "Points" INTEGER
                      );'''),
        ('Timeline', '''CREATE TABLE "Timeline" (
                            "CurSeason" INTEGER, 
                            "CurRound" INTEGER, 
                            "Entries" INTEGER, 
                            "Channel" INTEGER, 
                            "Role" INTEGER
                        );'''),
        ('UserCardEntries', '''CREATE TABLE "UserCardEntries" (
                                "DiscordID" TEXT UNIQUE PRIMARY KEY, 
                                "Cards" TEXT, 
                                "CardsText" TEXT, 
                                "CardImages" TEXT
                               );''')
    ]
    
    # Use context manager to handle connection and cursor
    with sqlite3.connect('3cb.db') as conn:
        cur = conn.cursor()
        
        # Check if the Timeline table exists
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name = 'Timeline'")
        if cur.fetchone() is None:
            # If Timeline does not exist, create all required tables
            for table_name, create_statement in tables_to_create:
                cur.execute(create_statement)
            
            # Insert initial data into the Timeline table
            cur.execute("INSERT INTO Timeline (CurSeason, CurRound, Entries, Channel) VALUES (0, 0, 0, 0)")
            print("Tables initialised.")
        else:
            print("Tables present.")

def load_entries_from_db(bot):
    """
    Loads all user entries from the database and creates EntryCards objects with in_db=True,
    then stores them in bot.entries using the user's Discord ID as the key.
    """
    with sqlite3.connect('3cb.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT DiscordID, Cards, CardsText, CardImages FROM UserCardEntries")
        rows = cur.fetchall()
        
        for row in rows:
            discord_id, cards, cardstext, cardimages = row
            # Create EntryCards object with in_db=True
            entry = EntryCards(discord_id, cards.split(','), cardstext.split(','), cardimages.split(','), in_db=True)
            # Store in bot.entries dictionary with Discord ID as the key
            bot.entries[str(discord_id)] = entry
    
    print(f"Loaded {len(bot.entries)} entries from the database.")


async def add_entries_to_db(bot):
    """
    Periodically checks bot.entries for entries that have in_db=False,
    adds them to the database, and updates their in_db status.
    """
    
    while True:
        if bot.state == 'entriesopen':
            for discord_id, entry in bot.entries.items():
                if not entry.in_db:
                    # Add entry to the database
                    with sqlite3.connect('3cb.db') as conn:
                        cur = conn.cursor()
                        cur.execute('''INSERT OR REPLACE INTO UserCardEntries (DiscordID, Cards, CardsText, CardImages)
                                    VALUES (?, ?, ?, ?)''', 
                                    (entry.user, ','.join(entry.cards), ','.join(entry.cardstext), ','.join(entry.cardimages)))
                        conn.commit()
                    
                    # Fetch the user object to get the username
                    user = bot.get_user(entry.user)
                    if user is not None:
                        print(f"Added or replaced entry for user {user.name} in the database.")
                    else:
                        print(f"Added or replaced entry for user ID {entry.user} in the database.")

                    # Update the entry's in_db status
                    entry.in_db = True
            
        # Wait for 15 seconds before scanning again
        await asyncio.sleep(15)
