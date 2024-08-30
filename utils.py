#util.py
#different bits and bobs to make it all run

import sqlite3
from EntryCards import EntryCards
import asyncio
from Battle import Battle

def initialise_db():
    """
    Checks the database and creates tables if they do not exist.
    """
    # SQL commands to create necessary tables
    tables_to_create = [
        ('Timeline', '''CREATE TABLE "Timeline" (
                            "CurSeason" INTEGER, 
                            "CurRound" INTEGER,
                            "Channel" INTEGER, 
                            "State" TEXT
                        );'''),
        ('UserCardEntries', '''CREATE TABLE "UserCardEntries" (
                                "DiscordID" TEXT UNIQUE PRIMARY KEY, 
                                "Cards" TEXT, 
                                "CardsText" TEXT, 
                                "CardImages" TEXT
                            );'''),
        ('Battles', '''CREATE TABLE "Battles" (
                        "ID" INTEGER PRIMARY KEY AUTOINCREMENT,
                        "BattleID" INTEGER UNIQUE,
                        "Player1ID" TEXT,
                        "Player2ID" TEXT,
                        "Resolved" INTEGER,
                        "PointsPlayer1" INTEGER,
                        "PointsPlayer2" INTEGER,
                        "PostID" TEXT
                    );'''),
        ('Standings', '''CREATE TABLE "Standings" (
                            "PlayerID" TEXT PRIMARY KEY, 
                            "Points" INTEGER
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
            cur.execute("INSERT INTO Timeline (CurSeason, CurRound, Channel, State) VALUES (0, 0, 0, 'startup')")
            print("Tables initialised.")
        else:
            print("Tables present.")

def load_entries_from_db(bot):
    """
    Loads all user entries from the database and creates EntryCards objects with in_db=True,
    then stores them in bot.entries using the user's Discord ID as the key.
    Also loads all battles from the database and creates Battle objects, storing them in bot.battles.
    """
    # Initialize bot entries and battles
    bot.entries = {}
    bot.battles = []
    try:
        with sqlite3.connect('3cb.db') as conn:
            cur = conn.cursor()

            # Load user entries
            cur.execute("SELECT DiscordID, Cards, CardsText, CardImages FROM UserCardEntries")
            rows = cur.fetchall()
            for row in rows:
                discord_id, cards, cardstext, cardimages = row
                # Create EntryCards object with in_db=True
                entry = EntryCards(discord_id, cards.split(','), cardstext.split(','), cardimages.split(','), in_db=True)
                # Store in bot.entries dictionary with Discord ID as the key
                bot.entries[str(discord_id)] = entry

            print(f"Loaded {len(bot.entries)} entries from the database.")

            # Load battles
            cur.execute("SELECT BattleID, Player1ID, Player2ID, Resolved, PointsPlayer1, PointsPlayer2, PostID FROM Battles")
            battles = cur.fetchall()
            for battle_row in battles:
                battle_id, player1_id, player2_id, resolved, points_player1, points_player2, post_id = battle_row
                # Create Battle object
                battle = Battle(
                    player1_id=player1_id,
                    player2_id=player2_id,
                    resolved=bool(resolved),
                    points_player1=points_player1,
                    points_player2=points_player2,
                )
                battle.post_id = post_id if post_id is not None else battle.post_id
                # Store in bot.battles list
                bot.battles.append(battle)
            
            print(f"Loaded {len(bot.battles)} battles from the database.")
    except Exception as e:
        print(f'Error loading from DB: {e}')


async def archivist(bot):
    """
    Syncs current bot state to the DB in case of failure.
    """
    prev_hash = None
    while True:
        if bot.state == 'entriesopen':
            for discord_id, entry in bot.entries.items():
                if not entry.in_db:
                    # Add entry to the database
                    with sqlite3.connect('3cb.db') as conn:
                        cur = conn.cursor()
                        cur.execute('''INSERT OR REPLACE INTO UserCardEntries (DiscordID, Cards, CardsText, CardImages)
                                    VALUES (?, ?, ?, ?)''', 
                                    (entry.user, ','.join(entry.cards), ','.join(entry.cardstext), ','.join(entry.cardsimages)))
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
        timeline_state = (bot.season, bot.round, bot.channel.id if bot.channel is not None else 0, bot.state)
        curr_hash = hash(timeline_state)
        if prev_hash is None:
            prev_hash = curr_hash
        # Generate a new hash using the built-in hash function
        

        # Check if the timeline state has changed by comparing hashes
        if curr_hash != prev_hash:
            # Update the Timeline table with the current bot state
            try:
                with sqlite3.connect('3cb.db') as conn:
                    cur = conn.cursor()
                    cur.execute('''UPDATE Timeline SET 
                                    CurSeason = ?, 
                                    CurRound = ?, 
                                    Channel = ?, 
                                    State = ?''',
                                (bot.season, bot.round, bot.channel.id if bot.channel is not None else 0, bot.state))
                    conn.commit()
                    print("Timeline table updated with the current bot state.")
            except Exception as e:
                print(f"Error updating Timeline table: {e}")
            prev_hash = curr_hash
        await asyncio.sleep(1)

def load_timeline_values(bot):
        """Loads values from the Timeline table and sets them as attributes on the bot."""
        try:
            with sqlite3.connect('3cb.db') as conn:
                cur = conn.cursor()
                cur.execute("SELECT CurSeason, CurRound, Channel, State FROM Timeline")
                result = cur.fetchone()
                if result:
                    # Set bot attributes
                    bot.season = result[0]
                    bot.round = result[1]
                    bot.channel = bot.get_channel(result[2])
                    bot.state = result[3]
                else:
                    # Set default values if nothing is found
                    bot.season = 0
                    bot.round = 0
                    bot.channel = bot.get_channel(993978824213672059)
                    bot.state = 'idle'
        except Exception as e:
            print(f"ohno {e}")
        print(f"Bot timeline values loaded: Season {bot.season}, Round {bot.round}, Channel {bot.channel}, State {bot.state}")

async def set_state(bot, new_state):
    """
    Change the state on the bot.
    """

    bot.state = new_state
    print(f"Bot state updated to: {bot.state}")