# Quick Start Guide

## Prerequisites

- Python 3.10 or higher
- A Discord bot token
- Your Discord channel ID where Wordle results are posted

## Setup Steps

### 1. Create a .env file

Copy the `.env.example` to `.env` and fill in your actual values:

```bash
cp .env.example .env
```

Then edit `.env` with your actual credentials:
```env
DISCORD_BOT_TOKEN=your_actual_bot_token_here
WORDLE_CHANNEL_ID=your_actual_channel_id_here
WORDLE_BOT_ID=903698786472009758
```

**IMPORTANT:** Never commit your `.env` file! It's already in `.gitignore`.

### 2. Install Dependencies

```bash
# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install required packages
pip install -r requirements.txt
```

### 3. Run the Bot

```bash
python bot.py
```

You should see output like:
```
==================================================
🤖 Wordle Discord Stats Bot
==================================================
✅ Commands registered
🚀 Starting bot...
✅ Bot is ready!
   Logged in as: YourBotName (ID: ...)
   Watching channel ID: ...
   Database: wordle_stats.db
   Command prefix: !
   Connected to 1 server(s)
==================================================
```

### 4. Backfill Historical Data

Once the bot is running, go to your Discord Wordle channel and run:

```
!backfill 200
```

This will import the last 200 messages from the Wordle bot. Only administrators can use this command.

## Available Commands

### Statistics Commands
- `!leaderboard` or `!lb` - Show wins leaderboard
- `!stats [@player]` - Show personal stats (defaults to you)
- `!average` or `!avg` - Show average scores for all players
- `!streak` - Show current and best group streaks
- `!luck` - Show luckiest players (1/6 and 2/6 scores)
- `!history [days]` - Show recent results (default: 7 days)

### Comparison Commands
- `!head2head @player1 @player2` or `!h2h` - Compare two players
- `!whowins` - Show who wins most on each weekday

### Visualization Commands
- `!chart leaderboard` - Wins leaderboard chart
- `!chart average` - Average scores chart
- `!chart luck` - Luckiest players chart
- `!chart participation` - Participation rate chart
- `!chartdist [@player]` - Score distribution for a player
- `!charth2h @player1 @player2` - Head-to-head comparison chart

### Admin Commands
- `!backfill [limit]` - Import historical Wordle results (admin only)
- `!dbstats` - Show database statistics

### Other Commands
- `!help_wordle` - Show all commands
- `!ping` - Check bot latency

## How It Works

1. **Automatic Tracking**: The bot listens for messages from the Wordle Discord bot in your configured channel
2. **Parsing**: It extracts scores, winners, and streak information
3. **Storage**: Results are saved to a SQLite database (`wordle_stats.db`)
4. **Commands**: You and your friends can query stats anytime using commands

## Troubleshooting

### Bot doesn't respond to commands
- Make sure the bot has permission to read messages and send messages in the channel
- Check that you're using the correct command prefix (default: `!`)

### Bot doesn't detect Wordle results
- Verify `WORDLE_CHANNEL_ID` is correct
- Verify `WORDLE_BOT_ID` is correct (default: 903698786472009758)
- Check that Message Content Intent is enabled in Discord Developer Portal

### "Privileged intent" error
- Go to Discord Developer Portal → Your App → Bot
- Enable "MESSAGE CONTENT INTENT" under Privileged Gateway Intents

### Import errors
- Make sure you activated the virtual environment
- Run `pip install -r requirements.txt` again

## Testing the Parser

You can test the message parser independently:

```bash
python parser.py
```

This will run test cases and show you how different message formats are parsed.

## Database

The bot uses SQLite for storage. The database file is `wordle_stats.db` and is created automatically.

To view the database contents, you can use:
```bash
sqlite3 wordle_stats.db
```

Then run SQL queries like:
```sql
SELECT * FROM results ORDER BY date DESC LIMIT 10;
```

## Next Steps

- Deploy to a cloud service (Railway, Render, AWS) to keep it running 24/7
- Customize the bot's status message in `bot.py`
- Add more visualizations in `visualizations.py`
- Create custom commands in `commands.py`

## Support

If you encounter issues:
1. Check the console output for error messages
2. Verify your `.env` file has correct values
3. Make sure the bot has proper Discord permissions
4. Test the parser with `python parser.py`

Enjoy tracking your Wordle competition! 🎯
