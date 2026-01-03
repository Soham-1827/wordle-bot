"""
    Configuration and constants for the Wordle Discord Bot
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

 # Discord Configuration
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
WORDLE_CHANNEL_ID = int(os.getenv('WORDLE_CHANNEL_ID', 0))
WORDLE_BOT_ID = int(os.getenv('WORDLE_BOT_ID', 903698786472009758))

 # Bot Configuration
COMMAND_PREFIX = os.getenv('COMMAND_PREFIX', '!')

 # Database Configuration
DATABASE_PATH = os.getenv('DATABASE_PATH', 'wordle_stats.db')

 # Constants
CROWN_EMOJI = '👑'
SCORE_PATTERN = r'([👑]?\s*)?([X\d])/6:\s*(@[\w.]+(?:\s+@[\w.]+)*)'
STREAK_PATTERN = r'(\d+)\s+day\s+streak'

 # Score mapping (X/6 is stored as 7 for failed attempts)
FAIL_SCORE = 7

 # Validate required environment variables
if not DISCORD_BOT_TOKEN:
    raise ValueError("DISCORD_BOT_TOKEN is required in .env file")
if not WORDLE_CHANNEL_ID:
    raise ValueError("WORDLE_CHANNEL_ID is required in .env file")