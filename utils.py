#util.py
#different bits and bobs to make it all run

import sqlite3

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



