# 3CBBot 
## by Michael Leslie

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Project Structure](#project-structure)
4. [Installation](#installation)
5. [Setup and Configuration](#setup-and-configuration)
6. [Usage](#usage)
7. [Commands](#commands)
8. [Contributing](#contributing)
9. [License](#license)

## Overview

`3CBBot` is a Discord bot designed to facilitate playing the 3 Card Blind (3CB) format of Magic: The Gathering. This bot allows players to submit decks, manage pairings, and track match results automatically within a Discord server.

## Features

- **Deck Submission**: Players can submit their 3-card decks directly through Discord.
- **Automatic Pairing**: The bot generates pairings for matches and updates the results.
- **Score Management**: Tracks wins, losses, and draws for all matches.
- **Admin Commands**: Provides various admin commands for managing rounds, state, and more.
- **Persistent Data Storage**: Uses SQLite for storing deck submissions, match results, and state information.

## Project Structure
```
3CBBot/ 
├── cogs/ # Directory containing bot cogs 
│ ├── controls.py # Cog for admin commands and bot control 
│ ├── entries.py # Cog for player deck submissions 
│ └── voting.py # Cog for managing voting and scoring 
├── utils.py # Utility functions for database and bot operations 
├── pairing.py # Logic for generating match pairings 
├── testinput.py # Test input for simulating player entries 
├── main.py # Main entry point for the bot 
├── README.md # Documentation file 
├── pyproject.toml # Poetry configuration file for dependencies 
└── .env # Environment variables file (not included in the repository)
```

## Installation

To install and run `3CBBot`, you will need to have Python 3.8 or higher and Poetry installed on your system. Follow these steps to set up the project:

1. **Clone the Repository:**

    `git clone https://github.com/wildfire111/3cbbot.git`

2. **Install Poetry:**
    Using pip install Poetry, our virtual environment manager

    `pip install poetry`

3. **Install Dependencies:**
    Use Poetry to install the project's dependencies:

    `poetry install`

    This command will create a virtual environment and install all the required dependencies specified in the pyproject.toml file.

4. **Create a .env file:**

    Create a .env file in the root directory of the project to store your Discord bot token and other environment variables:

    `BOT_KEY=your_discord_bot_token`
    `ADMIN_ID=your_discord_id`

    Replace your_discord_bot_token with your bot's token and your_discord_id with your Discord user ID.

5. **Run the bot:**
    Start the bot using the following command:

    `poetry run python main.py`

    The bot should now be online and ready to use in your Discord server.

## Usage

Once the bot is running, it will listen for commands from users in your Discord server. The bot has both player commands for submitting decks and admin commands for managing the game.

#### Player Commands
* /enter `<card1>` `<card2>` `<card3>`: Submit a deck for the current round.
* /get-entry: Retrieve your current submitted deck.
#### Admin Commands (Dm to the bot)
* !getstate: Display the current state of the bot.
* !setstate `<state>`: Set a new state for the bot (e.g., entriesopen, paired, etc.).
* !newround: Start a new round, incrementing the round number and clearing previous entries.
* !pair: Generate match pairings for the current round.
* !vote: Start the voting process for battles.
* !deleteposts: Delete all posts related to battles.
* !fakeentries: Simulate fake entries for testing purposes.
* !channel `<channel_id>`: Set the bot's operating channel.
* !manualscore `<emoji>` `<battleid>`: Manually resolve a battle using the given emoji and battle ID.