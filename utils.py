#util.py
#different bits and bobs to make it all run

import sqlite3

def initialise_db():
    """
    checks the database and creates tables if they do not exist.
    """
    tables_to_create = [
        ('Points', '''CREATE TABLE "Points" ("Card" TEXT, "Points" INTEGER);'''),
        ('Timeline', '''CREATE TABLE "Timeline" (
                            "CurSeason" INTEGER, 
                            "CurRound" INTEGER, 
                            "Entries" INTEGER, 
                            "Channel" INTEGER, 
                            "Role" INTEGER
                        );'''),
        ('User', '''CREATE TABLE "User" (
                        "ID" INTEGER UNIQUE, 
                        "DiscordID" TEXT UNIQUE, 
                        "Active" INTEGER, 
                        PRIMARY KEY("ID" AUTOINCREMENT)
                    );''')
    ]
    
    #use context manager to handle connection and cursor
    with sqlite3.connect('3cb.db') as conn:
        cur = conn.cursor()
        
        #check if timeline table exists
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name = 'Timeline'")
        if cur.fetchone() is None:
            #if timeline does not exist, create all required tables
            for table_name, create_statement in tables_to_create:
                cur.execute(create_statement)
            
            #insert initial data
            cur.execute("INSERT INTO Timeline (CurSeason, CurRound, Entries, Channel) VALUES (0, 0, 0, 0)")
            print("Tables initialised.")
        else:
            print("Tables present.")



