import sqlite3
from EntryCards import EntryCards
import asyncio
from Battle import Battle
import logging

# Set up logging configuration
logging.basicConfig(level=logging.INFO)

def initialise_db():
    """
    Checks the database and creates tables if they do not exist.
    """
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
    
    with sqlite3.connect('3cb.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name = 'Timeline'")
        if cur.fetchone() is None:
            for table_name, create_statement in tables_to_create:
                cur.execute(create_statement)
            cur.execute("INSERT INTO Timeline (CurSeason, CurRound, Channel, State) VALUES (0, 0, 0, 'startup')")
            logging.info("Tables initialized.")
        else:
            logging.info("Tables already present.")

def load_entries_from_db(bot):
    """
    Loads all user entries from the database and creates EntryCards objects with in_db=True,
    then stores them in bot.entries using the user's Discord ID as the key.
    Also loads all battles from the database and creates Battle objects, storing them in bot.battles.
    """
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
                entry = EntryCards(discord_id, cards.split(','), cardstext.split(','), cardimages.split(','), in_db=True)
                bot.entries[str(discord_id)] = entry

            logging.info(f"Loaded {len(bot.entries)} entries from the database.")

            # Load battles
            cur.execute("SELECT BattleID, Player1ID, Player2ID, Resolved, PointsPlayer1, PointsPlayer2, PostID FROM Battles")
            battles = cur.fetchall()
            for battle_row in battles:
                battle_id, player1_id, player2_id, resolved, points_player1, points_player2, post_id = battle_row
                battle = Battle(
                    player1_id=player1_id,
                    player2_id=player2_id,
                    resolved=bool(resolved),
                    points_player1=points_player1,
                    points_player2=points_player2,
                )
                battle.post_id = post_id if post_id is not None else battle.post_id
                bot.battles.append(battle)
            
            logging.info(f"Loaded {len(bot.battles)} battles from the database.")
    except Exception as e:
        logging.error(f'Error loading from DB: {e}')

async def archivist(bot):
    """
    Syncs current bot state to the DB in case of failure.
    """
    prev_hash = None
    while True:
        if bot.state == 'entriesopen':
            for discord_id, entry in bot.entries.items():
                if not entry.in_db:
                    with sqlite3.connect('3cb.db') as conn:
                        cur = conn.cursor()
                        cur.execute('''INSERT OR REPLACE INTO UserCardEntries (DiscordID, Cards, CardsText, CardImages)
                                    VALUES (?, ?, ?, ?)''', 
                                    (entry.user, ','.join(entry.cards), ','.join(entry.cardstext), ','.join(entry.cardsimages)))
                        conn.commit()
                    
                    user = bot.get_user(entry.user)
                    if user:
                        logging.info(f"Added or replaced entry for user {user.name} in the database.")
                    else:
                        logging.info(f"Added or replaced entry for user ID {entry.user} in the database.")
                    entry.in_db = True
            
        timeline_state = (bot.season, bot.round, bot.channel.id if bot.channel else 0, bot.state)
        curr_hash = hash(timeline_state)
        if prev_hash is None:
            prev_hash = curr_hash

        if curr_hash != prev_hash:
            try:
                with sqlite3.connect('3cb.db') as conn:
                    cur = conn.cursor()
                    cur.execute('''UPDATE Timeline SET 
                                    CurSeason = ?, 
                                    CurRound = ?, 
                                    Channel = ?, 
                                    State = ?''',
                                (bot.season, bot.round, bot.channel.id if bot.channel else 0, bot.state))
                    conn.commit()
                    logging.info("Timeline table updated with the current bot state.")
            except Exception as e:
                logging.error(f"Error updating Timeline table: {e}")
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
                bot.season, bot.round, channel_id, bot.state = result
                bot.channel = bot.get_channel(channel_id)
            else:
                bot.season = 0
                bot.round = 0
                bot.channel = bot.get_channel(993978824213672059)
                bot.state = 'idle'
            logging.info(f"Bot timeline values loaded: Season {bot.season}, Round {bot.round}, Channel {bot.channel}, State {bot.state}")
    except Exception as e:
        logging.error(f"Error loading timeline values: {e}")

async def set_state(bot, new_state):
    """
    Change the state on the bot.
    """
    bot.state = new_state
    logging.info(f"Bot state updated to: {bot.state}")
