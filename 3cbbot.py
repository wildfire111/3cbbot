import discord
from discord.ext import commands
from discord.utils import get
import sqlite3
import asyncio
import logging
import requests

import os
from dotenv import load_dotenv
load_dotenv()
token = os.getenv('3CB_TOKEN')

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

#logging.basicConfig(filename='pricebotlog.txt', encoding='utf-8', level=print, format='%(asctime)s | %(levelname)s:%(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

@bot.event
async def on_ready():
    print("Bot online")
    user = await bot.fetch_user(248740105248964608)
    await user.send("Bot online.")
    conn = sqlite3.connect('3cb.db')
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name = 'Timeline'")
    if cur.fetchone() == None:
        cur.execute('CREATE TABLE "Points" ("Card" TEXT, "Points" INTEGER);')
        cur.execute('CREATE TABLE "Timeline" ("CurSeason"	INTEGER, "CurRound" INTEGER, "Entries" INTEGER, "Channel" INTEGER, "Role" INTEGER);')
        cur.execute('CREATE TABLE "User" ("ID" INTEGER UNIQUE, "DiscordID" TEXT UNIQUE, "Active" INTEGER, PRIMARY KEY("ID" AUTOINCREMENT));')
        cur.execute('CREATE TABLE "Temp" ("Card" TEXT)')
        cur.execute("INSERT INTO Timeline (CurSeason, CurRound, Entries, Channel) VALUES (0, 0, 0, 0)")
        cur.execute("INSERT INTO Temp (Card) VALUES ('Hello')")
        print("Essential tables not detected, created them.")
    else:
        print("Tables already exist.")
    conn.commit()
    cur.close()


#ENTRIES
@bot.listen('on_message')
async def directmessage(message):
    if message.author == bot.user or type(message.channel) != discord.channel.DMChannel:
        return
    content = message.content
    content = content.title()
    if message.author.id == 248740105248964608 and content[0] == "!":
        return
    conn = sqlite3.connect('3cb.db')
    cur = conn.cursor()
    cur.execute("Select Entries FROM Timeline")
    if cur.fetchone()[0] != 1:
        await message.channel.send("Sorry, entries are closed right now.")
        return
    user = message.author.id
    cur.execute(f"SELECT ID, Active from User WHERE DiscordID = {str(user)}")
    result = cur.fetchone()
    if result == None:
        await message.channel.send("Sorry, you're not enrolled. Please use !join in the 3CB channel.")
        return
    elif result[1] == 0:
        await message.channel.send("Sorry, you're not enrolled. Please use !join in the 3CB channel.")
        return
    userid = result[0]
    username = message.author.name
    print(f"{username} {content}")
    cur.execute("SELECT CurSeason, CurRound FROM Timeline")
    seasonround = cur.fetchone()
    cur.execute("UPDATE Temp SET Card = ?", (content,))
    conn.commit()
    cur.execute("SELECT Card FROM Temp")
    content = str(cur.fetchone()[0])
    cardtarget = "RoundentriesS"+str(seasonround[0])+"R"+str(seasonround[1])
    params = {"exact":content,"format":"image"}
    api = "https://api.scryfall.com/cards/named"
    response = requests.get(api,params=params)
    if response.status_code == 404:
        await message.channel.send("Sorry, card not found in Scryfall. Could you please check your spelling, and make sure it is Vintage legal.")
        return
    scryfalllink = response.url
    #print(scryfalllink)
    cur.execute(f"SELECT Card1, Card2, Card3 FROM {cardtarget} WHERE UserID = {str(userid)}")
    cards = cur.fetchone()
    if cards == None:
        cur.execute(f"INSERT INTO {cardtarget} (UserID, Card1, Card1URL) VALUES ({userid},?,'{scryfalllink}')", (content,))
        await message.channel.send("Your first card has been recorded as "+content+". Please enter your second card.")
    elif cards[2] != None:
        cur.execute(f"UPDATE {cardtarget} SET Card1 = ?, Card2 = Null, Card3 = Null, Card1URL = '{scryfalllink}' WHERE UserID = {str(userid)}", (content,))
        await message.channel.send("Your previous submission has been overridden and your first card has been recorded as "+content+". Please enter your second card.")
    elif cards[1] == None:
        cur.execute(f"UPDATE {cardtarget} SET Card2 = ?, Card2URL = '{scryfalllink}' WHERE UserID = {str(userid)}", (content,))
        await message.channel.send(f"Your second card has been recorded as {content}. Please enter your third card.")
    elif cards[2] == None:
        cur.execute(f"UPDATE {cardtarget} SET Card3 = ?, Card3URL = '{scryfalllink}' WHERE UserID = {str(userid)}", (content,))
        await message.channel.send(f"Your deck is currently recorded as {cards[0]}, {cards[1]} and {content}. If you want to submit a new deck, just enter a new card and it will overwrite your previous deck.")
        cur.execute(f"SELECT COUNT(ID) FROM User")
        count = cur.fetchone()[0]

        #if count >= 20:
        #    cur.execute("UPDATE Timeline SET Entries = 0")
        #    user = await bot.fetch_user(248740105248964608)
        #    await user.send("Max users reached, entries closed.")
    conn.commit()
    cur.close()
    print("added to db")

#JOIN
@bot.command()
async def join(ctx):
    role = "3CB Enjoyers"
    user = ctx.message.author
    discordid = ctx.message.author.id
    await user.add_roles(discord.utils.get(user.guild.roles, name=role))
    conn = sqlite3.connect('3cb.db')
    cur = conn.cursor()
    cur.execute(f"SELECT ID FROM User WHERE DiscordID = {str(discordid)}")
    if cur.fetchone() != None:
        cur.execute(f"UPDATE User SET Active = 1 WHERE DiscordID = {str(discordid)}")
    else:
        cur.execute(f"INSERT INTO User (DiscordID, Active) VALUES ({str(discordid)}, 1)")
    cur.execute("SELECT Entries FROM Timeline")
    entries = cur.fetchone()[0]
    if entries == 1:
        await user.send("Hi! Welcome to 3CB. Please enter your first card. If you need help, please use the !help command in 3CB Channel.")
    else:
        await user.send("Hi! Welcome to 3CB. Entries are closed, you will be pinged when they're open.")
    conn.commit()
    cur.close()
    print(f"user {ctx.message.author.name} added")

#LEAVE
@bot.command()
async def leave(ctx):
    try:
        user = ctx.message.author
        role_get = discord.utils.get(ctx.message.guild.roles, name='3CB Enjoyer')
        await user.remove_roles(role_get)
    except:
        logging.warning("Tried to use !leave, couldn't remove role")
    conn = sqlite3.connect('3cb.db')
    cur = conn.cursor()
    userid = ctx.message.author.id
    cur.execute(f"UPDATE User SET Active = 0 WHERE DiscordID = {str(userid)}")
    conn.commit()
    cur.close()

#NEWSEASON
@bot.command()
async def newseason(ctx):
    if ctx.author.id != 248740105248964608:
        return
    conn = sqlite3.connect('3cb.db')
    cur = conn.cursor()
    cur.execute("SELECT CurSeason FROM Timeline")
    curseason = cur.fetchone()[0]
    targetseason = curseason+1
    standingsname = "StandingsS"+str(targetseason)
    cur.execute(f"UPDATE Timeline SET CurSeason = {str(targetseason)}")
    cur.execute(f"CREATE TABLE {standingsname} ('ID' INTEGER, 'POINTS' INTEGER, PRIMARY KEY('ID' AUTOINCREMENT));")
    cur.execute(f"UPDATE Timeline SET CurRound = 0, Entries = 0")
    conn.commit()
    cur.close()
    user = await bot.fetch_user(248740105248964608)
    await user.send(f"Season {str(targetseason)} created. !newround next.")

#NEWROUND
@bot.command()
async def newround(ctx):
    if ctx.author.id != 248740105248964608:
        return
    conn = sqlite3.connect('3cb.db')
    cur = conn.cursor()
    cur.execute("Select CurRound, Channel FROM Timeline")
    roundchannel = cur.fetchone()
    channelid = roundchannel[1]
    if channelid == 0:
        await ctx.send("Channel not set")
        return
    curround = roundchannel[0]
    curround = curround + 1
    cur.execute("UPDATE Timeline SET CurRound = CurRound + 1, Entries = 0")
    cur.execute("SELECT CurSeason FROM Timeline")
    curseason = cur.fetchone()[0]
    tablename = "RoundentriesS"+str(curseason)+"R"+str(curround)
    cur.execute(f'''CREATE TABLE {tablename}
        ('ID' INTEGER UNIQUE,
        'UserID' INTEGER UNIQUE,
        'Card1' TEXT,
        'Card2' TEXT,
        'Card3' TEXT,
        'Card1URL' TEXT,
        'Card2URL' TEXT,
        'Card3URL' TEXT,
        'Roundpoints' INTEGER,
        PRIMARY KEY('ID' AUTOINCREMENT));''')
    tablename = "Round"+str(curround)
    user = await bot.fetch_user(248740105248964608)
    await user.send("Round "+str(curround)+" created. !entries to open entries next.")
    channel = await bot.fetch_channel(channelid)
    cur.execute("SELECT * FROM Points ORDER BY Points DESC")
    pointed = cur.fetchall()
    print(pointed)
    if pointed == []:
        tosend = '''Hello <@&1006150320826634331>, a new round has been created and entries are now open!\n
If you don't have the 3CB Enjoyers role, use !join\n
To submit a deck, DM the 3CBbot'''
    else:
        tosend = '''Hello <@&1006150320826634331>, a new round has been created and entries are now open!\n
If you don't have the 3CB Enjoyers role, use !join\n
To submit a deck, DM the 3CBbot\n
Please note that the following cards have points for this round, and you are only allowed 3 points maximum in your deck.\n```\n'''
        for card,points in pointed:
            tosend = tosend+f"{points} | {card}\n"
        tosend = tosend + '''```Note: If you have more than 3 points, you lose all your matches!'''
    await channel.send(tosend)
    cur.execute("UPDATE Timeline SET Entries = 1")
    conn.commit()
    cur.close()


#ENTRIES OPEN/CLOSE
@bot.command()
async def close(ctx):
    if ctx.author.id != 248740105248964608:
        return
    conn = sqlite3.connect('3cb.db')
    cur = conn.cursor()
    cur.execute("UPDATE Timeline SET Entries = 0")
    conn.commit()
    cur.close()
    await ctx.send("Entries closed")

#COUNT
@bot.command()
async def count(ctx):
    conn = sqlite3.connect('3cb.db')
    cur = conn.cursor()
    cur.execute("SELECT CurSeason, CurRound FROM Timeline")
    seasonround = cur.fetchone()
    curseason = seasonround[0]
    curround = seasonround[1]
    roundname = f"roundentriesS{curseason}R{curround}"
    cur.execute(f"SELECT COUNT(Card3) FROM {roundname} WHERE Card3 IS NOT NULL")
    count = cur.fetchone()[0]
    conn.commit()
    cur.close()
    await ctx.send(f"Players with decks submitted: {count}")

#PAIRINGS
@bot.command()
async def pair(ctx):
    if ctx.author.id != 248740105248964608:
        return
    conn = sqlite3.connect('3cb.db')
    cur = conn.cursor()
    cur.execute("SELECT CurSeason, Channel FROM Timeline")
    result = cur.fetchone()
    curseason = str(result[0])
    channelid = result[1]
    if channelid == 0:
        print("No channel set")
        await ctx.send("No channel set")
        return
    channel = await bot.fetch_channel(channelid)
    cur.execute("SELECT CurRound FROM Timeline")
    curround = str(cur.fetchone()[0])
    if curround == "0" or curseason == "0":
        print("Season hasn't started yet!")
        return
    else:
        print(f"Generating pairings for S{curseason}R{curround}")
    roundpairingsname = "roundpairingsS" + curseason + "R" + curround
    roundname = "roundentriesS" + curseason + "R" + curround
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name = ?", (roundpairingsname,))
    if cur.fetchone() != None:
        print("Round already paired.")
        return
    cur.execute(f'''CREATE TABLE {roundpairingsname} (
    "ID"	INTEGER,
    "Player1ID"	INTEGER,
    "Player2ID"	INTEGER,
    "DisMessID" INTEGER,
    PRIMARY KEY("ID" AUTOINCREMENT));''')
    conn.commit()
    cur.execute(f"SELECT UserID FROM {roundname} WHERE Card3 != ''")
    playerlist = cur.fetchall()
    for idtuple in playerlist:
        id = idtuple[0]
        for oppidtuple in playerlist:
            oppid = oppidtuple[0]
            if id == oppid:
                continue
            cur.execute(f"SELECT Player1ID, Player2ID FROM {roundpairingsname}")
            pairings = cur.fetchall()
            found = False
            for battle in pairings:
                if battle[0] == id and battle[1] == oppid:
                    #print("Pairing already exists")
                    found = True
                elif battle[1] == id and battle[0] == oppid:
                    #print("Pairing already exists reversed")
                    found = True
            if found == False:
                cur.execute(f"INSERT INTO {roundpairingsname} (Player1ID, Player2ID) VALUES ({id},{oppid})")
                #print("Pairing not found, added")
    cur.execute(f"SELECT Player1ID, Player2ID, ID FROM {roundpairingsname} ORDER BY ID ASC")
    battles = cur.fetchall()
    for battle in battles:
        cur.execute(f"SELECT DiscordID FROM User WHERE ID = {str(battle[0])}")
        battler1id = cur.fetchone()[0]
        cur.execute(f"SELECT DiscordID FROM User WHERE ID = {str(battle[1])}")
        battler2id = cur.fetchone()[0]
        cur.execute(f"SELECT Card1, Card2, Card3, Card1URL, Card2URL, Card3URL FROM {roundname} WHERE UserID = {str(battle[0])}")
        battler1cards = list(cur.fetchone())
        cur.execute(f"SELECT Card1, Card2, Card3, Card1URL, Card2URL, Card3URL FROM {roundname} WHERE UserID = {str(battle[1])}")
        battler2cards = list(cur.fetchone())
        try:
            battler1user = await bot.fetch_user(battler1id)
            battler1name = battler1user.name
        except:
            battler1name = "Unknown"
        try:
            battler2user = await bot.fetch_user(battler2id)
            battler2name = battler2user.name
        except:
            battler2name = "Unknown"
        battler1name = "A: "+battler1name
        battler2name = "B: "+battler2name
        embedtitle = "Pairing #"+str(battle[2])
        embed=discord.Embed(title=embedtitle, color=discord.Color.blue())
        cards = f"[{battler1cards[0]}]({battler1cards[3]})\n[{battler1cards[1]}]({battler1cards[4]})\n[{battler1cards[2]}]({battler1cards[5]})"
        embed.add_field(name=battler1name,value=cards)
        cards = f"[{battler2cards[0]}]({battler2cards[3]})\n[{battler2cards[1]}]({battler2cards[4]})\n[{battler2cards[2]}]({battler2cards[5]})"
        embed.add_field(name=battler2name,value=cards)
        footer = '''Please react as follows:\n
🅰️: Player A won both games\n
⬅️: Player A won a game and drew the other\n
🆎: Both players won a game\n
❌: Both games were a draw\n
➡️: Player B won a game and drew the other\n
🅱️: Player B won both games
'''
        if battler1id == 248740105248964608:
            footer = f"{footer}\nWith gasps of amazement at how anyone could come up with as cool a deck as player A's."
        embed.set_footer(text=footer)
        message = await channel.send(embed=embed)
        cur.execute(f"UPDATE {roundpairingsname} SET DisMessID = {message.id} WHERE Player1ID = {battle[0]} AND Player2ID = {battle[1]}")
    cur.execute(f"SELECT DisMessID FROM {roundpairingsname}")
    messageids = cur.fetchall()
    conn.commit()
    cur.close()
    for messageid in messageids:
        reactmsg = await channel.fetch_message(messageid[0])
        #await reactmsg.add_reaction("1\N{variation selector-16}\N{combining enclosing keycap}")
        await reactmsg.add_reaction("🅰️")
        await reactmsg.add_reaction("⬅️")
        await reactmsg.add_reaction("🆎")
        await reactmsg.add_reaction("❌")
        await reactmsg.add_reaction("➡️")
        await reactmsg.add_reaction("🅱️")

#listening to reactions
@bot.event
async def on_raw_reaction_add(ctx):
    if ctx.user_id == 986255468760551425:
        return
    if (
        ctx.emoji.name != '🅰️' and
        ctx.emoji.name != '⬅️' and
        ctx.emoji.name != '🆎' and
        ctx.emoji.name != '❌' and
        ctx.emoji.name != '➡️' and
        ctx.emoji.name != '🅱️'):
            return
    print("Emoji registered")
    conn = sqlite3.connect('3cb.db')
    cur = conn.cursor()
    cur.execute('SELECT Channel, CurSeason, CurRound FROM Timeline')
    chanseasround = cur.fetchone()
    channelid = chanseasround[0]
    curseason = chanseasround[1]
    curround = chanseasround[2]
    channel = bot.get_channel(channelid)
    msg = await channel.fetch_message(ctx.message_id)
    if ctx.channel_id == channelid:
        cur.execute(f"SELECT DisMessID from RoundpairingsS{curseason}R{curround}")
        messageids = cur.fetchall()
        print("Channel ID found")
        if (ctx.message_id,) in messageids:
            cur.execute(f"SELECT Player1ID, Player2ID FROM RoundpairingsS{curseason}R{curround} WHERE DisMessID = {ctx.message_id}")
            players = cur.fetchone()
            reaction = discord.utils.get(msg.reactions, emoji=ctx.emoji.name)
            print("Message ID found")
            if ctx.user_id == 248740105248964608 or reaction.count > 3:
                if ctx.emoji.name == '🅰️':
                    addpoints(players[0],3)
                    addpoints(players[1],0)
                    await msg.delete()
                    #Player 1 wins both
                elif ctx.emoji.name == '⬅️':
                    addpoints(players[0],1)
                    addpoints(players[1],0)
                    await msg.delete()
                    #Player 1 wins 1 and draws 1
                elif ctx.emoji.name == '🆎':
                    addpoints(players[0],1)
                    addpoints(players[1],1)
                    await msg.delete()
                    #each player wins one
                elif ctx.emoji.name == '➡️':
                    addpoints(players[1],1)
                    addpoints(players[0],0)
                    await msg.delete()
                    #player 2 wins 1 and draws 1
                elif ctx.emoji.name == '🅱️':
                    addpoints(players[1],3)
                    addpoints(players[0],0)
                    await msg.delete()
                    #player 2 wins both
                elif ctx.emoji.name == '❌':
                    addpoints(players[0],0)
                    addpoints(players[1],0)
                    await msg.delete()
                    #both players draw each game
    conn.commit()
    cur.close()


def addpoints(userid, points):
    print("Adding points.")
    conn = sqlite3.connect('3cb.db')
    cur = conn.cursor()
    cur.execute(f"SELECT CurSeason, CurRound FROM Timeline")
    seasonround = cur.fetchone()
    curround = seasonround[1]
    curseason = seasonround[0]
    if curseason == None:
        logging.warning("no season, can't add points")
        return
    cur.execute(f"SELECT Points FROM StandingsS{curseason} WHERE ID = {userid}")
    StandingsPoints = cur.fetchone()
    if StandingsPoints == None:
        cur.execute(f"INSERT INTO StandingsS{curseason} (ID, Points) VALUES ({userid}, {points})")
    else:
        cur.execute(f"UPDATE StandingsS{curseason} SET Points = Points + {points} WHERE ID = {userid}")
    cur.execute(f"SELECT Roundpoints FROM roundentriesS{curseason}R{curround} WHERE UserID = {userid}")
    roundpointssql = cur.fetchone()
    print(f"Len: {len(roundpointssql)}, {roundpointssql}")
    if roundpointssql[0] == None:
        cur.execute(f"UPDATE RoundentriesS{curseason}R{curround} SET Roundpoints = {points} WHERE UserID = {userid}")
        print("a")
    else:
        cur.execute(f"UPDATE RoundentriesS{curseason}R{curround} SET Roundpoints = Roundpoints + {points} WHERE UserID = {userid}")
        print("b")
    conn.commit()
    cur.close()

@bot.command()
async def endround(ctx):
    if ctx.author.id != 248740105248964608:
        return
    conn = sqlite3.connect('3cb.db')
    cur = conn.cursor()
    cur.execute(f"SELECT CurSeason, CurRound FROM Timeline")
    seasonround = cur.fetchone()
    curseason = seasonround[0]
    curround = seasonround[1]
    cur.execute(f"SELECT Card1, Card2, Card3 FROM roundentriesS{curseason}R{curround} ORDER BY Roundpoints DESC LIMIT 2")
    results = cur.fetchall()
    for deck in results:
        for card in deck:
            #cur.execute(f"SELECT Card, Points FROM Points WHERE Card = '{card}'")
            cur.execute(f"SELECT Card, Points FROM Points WHERE Card = ?", (card,))
            #cur.execute(f"UPDATE {cardtarget} SET Card2 = ?, Card2URL = '{scryfalllink}' WHERE UserID = {str(userid)}", (content,))
            cardpoints = cur.fetchone()
            if cardpoints == None:
                cur.execute(f"INSERT INTO Points (Card, Points) VALUES (?,1)", (card,))
            else:
                cur.execute(f"UPDATE Points SET Points = Points + 1 WHERE Card = ?", (card,))
        conn.commit()
    cur.execute(f"SELECT UserID, Roundpoints, Card1, Card2, Card3 FROM roundentriesS{curseason}R{curround} ORDER BY Roundpoints DESC")
    results = cur.fetchall()
    toprint = "```\nROUND STANDINGS\nRank - User(Round Points)\n"
    rank = 0
    for user in results:
        userid = user[0]
        roundpoints = user[1]
        card1 = user[2]
        card2 = user[3]
        card3 = user[4]
        cur.execute(f"SELECT DiscordID FROM User WHERE ID = {userid}")
        discorduserid = cur.fetchone()[0]
        try:
            user = await bot.fetch_user(discorduserid)
            username = user.name
        except:
            username = "Unknown"
        rank = rank + 1
        toprint = f"{toprint}#{rank} - {username}({roundpoints})\n    {card1}/{card2}/{card3}\n"
    conn.commit()
    cur.close()
    toprint = f"{toprint}\n```"
    await ctx.send(toprint)

@bot.command()
async def standings(ctx):
    if ctx.author.id != 248740105248964608:
        return
    conn = sqlite3.connect('3cb.db')
    cur = conn.cursor()
    cur.execute("SELECT CurSeason FROM Timeline")
    season = cur.fetchone()[0]
    cur.execute(f"SELECT * FROM StandingsS{season} ORDER BY Points DESC")
    standingslist = cur.fetchall()
    longest = 0
    for id, score in standingslist:
        if len(str(score)) > longest:
            longest = len(str(score))
    embedline = "```Points | Name\n"
    for id,score in standingslist:
        cur.execute(f"SELECT DiscordID FROM User WHERE ID = {id}")
        discordid = cur.fetchone()[0]
        try:
            user = await bot.fetch_user(discordid)
            username = str(user.name)
        except:
            username = "Unknown"
        if longest >= 3:
            embedline = embedline + "  " + str(score) + "  | "
        elif longest == 2:
            embedline = embedline + "  " + str(score) + "   | "
        elif longest <=1:
            embedline = embedline + "   " + str(score) + "   | "
        embedline = embedline + username + "\n"
    embedline = embedline+"\n```"
    conn.commit()
    cur.close()
    await ctx.send(embedline)
    print(f"sent standings to {ctx.author.name}")

@bot.command()
async def rank(ctx):
    conn = sqlite3.connect('3cb.db')
    cur = conn.cursor()
    cur.execute("SELECT CurSeason FROM Timeline")
    season = cur.fetchone()[0]
    discordid = ctx.author.id
    cur.execute(f"SELECT ID FROM User WHERE DiscordID = {discordid}")
    userid = cur.fetchone()[0]
    cur.execute(f"SELECT * FROM StandingsS{season} ORDER BY Points DESC")
    playerlist = cur.fetchall()
    count = 0
    for standingid,points in playerlist:
        count = count+1
        if userid == standingid:
            await ctx.send(f"{ctx.author.name} is currently ranked #{count}")
    print(f"sent rank to {ctx.author.name}")
    conn.commit()
    cur.close()

@bot.command()
async def setchannel(ctx):
    if ctx.author.id != 248740105248964608:
        return
    role = "3CB Enjoyers"
    user = ctx.message.author
    roleobj = discord.utils.get(user.guild.roles, name=role)
    roleid = roleobj.id
    channel = ctx.channel
    channelid = channel.id
    conn = sqlite3.connect('3cb.db')
    cur = conn.cursor()
    cur.execute(f"UPDATE Timeline SET Channel = {channelid}, Role = {roleid}")
    conn.commit()
    cur.close()
    channel = bot.get_channel(channelid)
    await channel.send("This channel set as default")

@bot.command()
async def help(ctx):
    await ctx.send(f"DMed you {ctx.author.mention}")
    user = ctx.message.author
    await user.send('''
    To enter the tournament, use !join in the tournament channel.\n
    For rules, use !rules.\n
    To see season standings, use !standings (not accurate while games are being scored)\n
    To see just your rank, use !rank
    If you have any issues with the bot otherwise, please message Wildfire#2345
    ''')
    print(f"sent help to {ctx.author.name}")

@bot.command()
async def rules(ctx):
    await ctx.send(f"DMed you {ctx.author.mention}")
    print(f"sent rules to {ctx.author.name}")
    user = ctx.message.author
    await user.send('''\nRULES OF 3CB\n
3CB is a 3 card Magic format traditionally played on forums. This bot is an attempt to port that game to Discord.\n\n
The game is played over a number of rounds comprising a season.
Players start a round by secretly submitting a deck of 3 vintage legal cards to 3CBbot, cards with the same name are allowed.\n
Decks may not contain more than 3 points worth of cards. Seasons begin with no pointed cards, but successful cards gain points for following rounds.
Each player then is paired against every other player in the round and two games are played, one where they are on the play and the other on the draw.\n
Each player starts a game on 20 life and by drawing 3 cards. You do not lose for drawing a card with an empty library, but you do draw a card every turn.\n
Games are played with perfect information, and random effects always result in the most beneficial way for the owners opponent.\n
Scoring is as follows. Each game win awards one point, with an additional bonus point for winning both games. Draws are scored as losses.\n
Some examples: If you win a game and draw/lose a game, you get 1 point. If you win both, you get 3. If you draw or lose both games, you get 0. Both players will get 1 point if they each win one game in a match.
The top two decks get 1 point put on each of their cards for each appearance they make, which affects the following round. Points accumulate.
''')

@bot.command()
async def fake(ctx, loop: int):
    if ctx.author.id != 248740105248964608:
        return
    iter = 1000000
    conn = sqlite3.connect('3cb.db')
    cur = conn.cursor()
    cur.execute("SELECT CurSeason, CurRound FROM Timeline")
    seasonround = cur.fetchone()
    cardtarget = "RoundentriesS"+str(seasonround[0])+"R"+str(seasonround[1])
    for x in range(loop):
        cur.execute(f"INSERT INTO User (DiscordID, Active) VALUES ({iter},1)")
        cur.execute(f"SELECT ID FROM User WHERE DiscordID = {iter}")
        userid = cur.fetchone()[0]
        cur.execute(f"INSERT INTO {cardtarget} (UserID, Card1, Card2, Card3, Card1URL, Card2URL, Card3URL) VALUES ({userid}, '{str(iter+1)}', '{str(iter+2)}', '{str(iter+3)}','www.google.com.au','www.google.com.au','www.google.com.au')")
        iter = iter+4
        conn.commit()
    conn.commit()
    cur.close()

bot.run(token)
