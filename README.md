# Wordle Discord Stats Bot 🎯

A Discord bot that automatically tracks your group's Wordle competition and provides stats & visualizations.

## What It Does

- 🤖 Listens for Wordle bot messages in your Discord server
- 📊 Tracks wins, scores, streaks, and participation
- 📈 Generates charts and leaderboards
- ⚔️ Head-to-head player comparisons

## Quick Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Create `.env` file:**
   ```env
   DISCORD_BOT_TOKEN=your_bot_token
   WORDLE_CHANNEL_ID=your_channel_id
   WORDLE_BOT_ID=903698786472009758
   ```

3. **Run the bot:**
   ```bash
   python bot.py
   ```

4. **Import history (in Discord):**
   ```
   !backfill 5000
   ```

## Commands

| Command | Description |
|---------|-------------|
| `!leaderboard` | Show wins leaderboard |
| `!stats [player]` | Personal stats |
| `!chart participation` | Who plays most consistently |
| `!chart leaderboard` | Wins chart |
| `!h2h player1 player2` | Head-to-head comparison |
| `!luck` | Luckiest players (1/6, 2/6 scores) |
| `!streak` | Current and best streaks |
| `!players` | List all tracked players |
| `!help_wordle` | Full command list |

## Features

✅ Automatic result tracking
✅ Multiple chart types
✅ Participation tracking
✅ Historical data import
✅ Tie handling
✅ SQLite storage

## Built With

- Python 3.10+
- discord.py
- matplotlib
- SQLite

---

Built by Soham and Claude 🤖
