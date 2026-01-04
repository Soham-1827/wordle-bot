"""
Main bot file for the Wordle Discord Stats Bot
"""
import discord
from discord.ext import commands
import asyncio
from datetime import datetime, timedelta

import config
import database
import parser
from commands import setup_commands


# Set up bot with intents
intents = discord.Intents.default()
intents.message_content = True  # Required to read message content
intents.messages = True
intents.guilds = True

# Create bot instance
bot = commands.Bot(
    command_prefix=config.COMMAND_PREFIX,
    intents=intents,
    help_command=None  # We'll use our custom help command
)


@bot.event
async def on_ready():
    """Called when the bot is ready"""
    print(f"✅ Bot is ready!")
    print(f"   Logged in as: {bot.user.name} (ID: {bot.user.id})")
    print(f"   Watching channel ID: {config.WORDLE_CHANNEL_ID}")
    print(f"   Database: {config.DATABASE_PATH}")
    print(f"   Command prefix: {config.COMMAND_PREFIX}")
    print(f"   Connected to {len(bot.guilds)} server(s)")
    print("=" * 50)

    # Set bot status
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=f"Wordle results | {config.COMMAND_PREFIX}help_wordle"
        )
    )


async def resolve_user_id_to_name(user_identifier: str, guild) -> tuple:
    """
    Resolve a user ID to a username, or return the identifier as-is if it's already a name

    Args:
        user_identifier: Either a Discord user ID (numeric string) or a username
        guild: The Discord guild/server object

    Returns:
        Tuple of (display_name, user_id)
    """
    # Check if it's a numeric ID
    if user_identifier.isdigit():
        try:
            user_id = int(user_identifier)
            member = guild.get_member(user_id)

            if member:
                # Use display name (nickname if set, otherwise username)
                return (member.display_name, str(user_id))
            else:
                # Try to fetch the user if not in cache
                try:
                    user = await bot.fetch_user(user_id)
                    return (user.name, str(user_id))
                except:
                    # If we can't find the user, use the ID as the name
                    return (user_identifier, user_identifier)
        except:
            return (user_identifier, None)
    else:
        # It's already a username
        return (user_identifier, None)


@bot.event
async def on_message(message):
    """Called when a message is sent in any channel the bot can see"""

    # Ignore messages from the bot itself
    if message.author.id == bot.user.id:
        return

    # Check if message is from the Wordle bot in the correct channel
    if message.author.id == config.WORDLE_BOT_ID and message.channel.id == config.WORDLE_CHANNEL_ID:
        print(f"\n📨 Received message from Wordle bot:")
        print(f"   Content: {message.content[:100]}...")

        # Try to parse the message
        results, streak, wordle_number = parser.parse_wordle_message(message.content)

        if results and parser.validate_results(results):
            # Get the date (assuming results are for "yesterday")
            date = parser.get_date_from_timestamp(message.created_at, is_yesterday=True)

            print(f"   ✅ Parsed {len(results)} results for {date}")
            print(f"   Streak: {streak}")

            # Save each result to database
            saved_count = 0
            for result in results:
                # Resolve user ID to username if needed
                player_name, player_id = await resolve_user_id_to_name(
                    result.player_name,
                    message.guild
                )

                success = database.save_result(
                    date=date,
                    player_name=player_name,
                    score=result.score,
                    is_winner=result.is_winner,
                    streak_day=streak or 0,
                    player_id=player_id,
                    wordle_number=wordle_number
                )

                if success:
                    saved_count += 1
                    print(f"      - Saved: {player_name} ({player_id if player_id else 'no ID'})")
                else:
                    print(f"      - Duplicate: {player_name}")

            # React to the message to confirm processing
            if saved_count > 0:
                await message.add_reaction('✅')
                print(f"   💾 Saved {saved_count}/{len(results)} results to database")
            else:
                await message.add_reaction('⚠️')
                print(f"   ⚠️ All results were duplicates")

        else:
            print(f"   ⚠️ Could not parse message or invalid results")

    # Process commands (this must be at the end)
    await bot.process_commands(message)


@bot.event
async def on_command_error(ctx, error):
    """Handle command errors"""
    if isinstance(error, commands.CommandNotFound):
        return  # Ignore unknown commands silently

    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Missing required argument: `{error.param.name}`")

    elif isinstance(error, commands.BadArgument):
        await ctx.send(f"❌ Invalid argument provided. Check the command usage.")

    else:
        # Log unexpected errors
        print(f"❌ Error in command '{ctx.command}': {error}")
        await ctx.send(f"❌ An error occurred: {str(error)}")


@bot.command(name='backfill')
@commands.has_permissions(administrator=True)
async def backfill(ctx, limit: int = 100):
    """
    Backfill historical Wordle results from this channel

    Usage: !backfill [limit]
    Note: Only administrators can use this command
    """
    if ctx.channel.id != config.WORDLE_CHANNEL_ID:
        await ctx.send("❌ This command can only be used in the Wordle channel!")
        return

    msg = await ctx.send(f"🔄 Starting backfill of up to {limit} messages...")

    processed = 0
    saved = 0
    duplicates = 0
    errors = 0

    try:
        async for message in ctx.channel.history(limit=limit):
            # Only process messages from the Wordle bot
            if message.author.id != config.WORDLE_BOT_ID:
                continue

            processed += 1

            # Parse the message
            results, streak, wordle_number = parser.parse_wordle_message(message.content)

            if results and parser.validate_results(results):
                date = parser.get_date_from_timestamp(message.created_at, is_yesterday=True)

                for result in results:
                    # Resolve user ID to username if needed
                    player_name, player_id = await resolve_user_id_to_name(
                        result.player_name,
                        ctx.guild
                    )

                    success = database.save_result(
                        date=date,
                        player_name=player_name,
                        score=result.score,
                        is_winner=result.is_winner,
                        streak_day=streak or 0,
                        player_id=player_id,
                        wordle_number=wordle_number
                    )

                    if success:
                        saved += 1
                    else:
                        duplicates += 1
            else:
                if '/6' in message.content:  # Only count as error if it looks like a result
                    errors += 1

        # Update the message with results
        await msg.edit(
            content=f"✅ **Backfill Complete!**\n"
                    f"Processed: {processed} Wordle bot messages\n"
                    f"Saved: {saved} new results\n"
                    f"Duplicates: {duplicates}\n"
                    f"Parse errors: {errors}"
        )

    except Exception as e:
        await msg.edit(content=f"❌ Backfill failed: {str(e)}")
        print(f"Backfill error: {e}")


@bot.command(name='dbstats')
async def db_stats(ctx):
    """
    Show database statistics

    Usage: !dbstats
    """
    import sqlite3
    conn = sqlite3.connect(config.DATABASE_PATH)
    c = conn.cursor()

    # Get total results
    c.execute('SELECT COUNT(*) FROM results')
    total_results = c.fetchone()[0]

    # Get unique players
    c.execute('SELECT COUNT(DISTINCT player_name) FROM results')
    unique_players = c.fetchone()[0]

    # Get date range
    c.execute('SELECT MIN(date), MAX(date) FROM results')
    min_date, max_date = c.fetchone()

    # Get total days tracked
    c.execute('SELECT COUNT(DISTINCT date) FROM results')
    total_days = c.fetchone()[0]

    conn.close()

    embed = discord.Embed(
        title="📊 Database Statistics",
        color=discord.Color.blue()
    )

    embed.add_field(name="Total Results", value=str(total_results), inline=True)
    embed.add_field(name="Unique Players", value=str(unique_players), inline=True)
    embed.add_field(name="Days Tracked", value=str(total_days), inline=True)

    if min_date and max_date:
        embed.add_field(name="First Date", value=min_date, inline=True)
        embed.add_field(name="Latest Date", value=max_date, inline=True)

    await ctx.send(embed=embed)


@bot.command(name='ping')
async def ping(ctx):
    """
    Check bot latency

    Usage: !ping
    """
    latency = round(bot.latency * 1000)
    await ctx.send(f"🏓 Pong! Latency: {latency}ms")


@bot.command(name='players', aliases=['list', 'names'])
async def list_players(ctx):
    """
    Show all player names in the database

    Usage: !players
    """
    import sqlite3
    conn = sqlite3.connect(config.DATABASE_PATH)
    c = conn.cursor()

    c.execute('''
        SELECT DISTINCT player_name, COUNT(*) as games
        FROM results
        GROUP BY player_name
        ORDER BY games DESC
    ''')

    players = c.fetchall()
    conn.close()

    if not players:
        await ctx.send("No players found in database!")
        return

    embed = discord.Embed(
        title="👥 Players in Database",
        color=discord.Color.blue(),
        description="Use these exact names for commands like !stats and !h2h"
    )

    player_list = []
    for player_name, games in players:
        player_list.append(f"**{player_name}** ({games} games)")

    # Split into chunks if too many players
    chunk_size = 10
    for i in range(0, len(player_list), chunk_size):
        chunk = player_list[i:i+chunk_size]
        embed.add_field(
            name=f"Players {i+1}-{min(i+chunk_size, len(players))}",
            value="\n".join(chunk),
            inline=False
        )

    await ctx.send(embed=embed)


def main():
    """Main entry point"""
    print("=" * 50)
    print("🤖 Wordle Discord Stats Bot")
    print("=" * 50)

    # Register commands
    setup_commands(bot)
    print("✅ Commands registered")

    # Start the bot
    print("🚀 Starting bot...")
    try:
        bot.run(config.DISCORD_BOT_TOKEN)
    except discord.LoginFailure:
        print("❌ Failed to login. Check your DISCORD_BOT_TOKEN in .env")
    except Exception as e:
        print(f"❌ Error starting bot: {e}")


if __name__ == "__main__":
    main()
