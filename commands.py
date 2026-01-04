"""
Bot commands for the Wordle Discord Stats Bot
"""
import discord
from discord.ext import commands
import database
import visualizations
from typing import Optional


def setup_commands(bot: commands.Bot):
    """Register all bot commands"""

    @bot.command(name='leaderboard', aliases=['lb', 'winners'])
    async def leaderboard(ctx, limit: int = 10):
        """
        Show the wins leaderboard

        Usage: !leaderboard [limit]
        Example: !leaderboard 5
        """
        data = database.get_leaderboard(limit)

        if not data:
            await ctx.send("No data available yet! Play some Wordle first!")
            return

        embed = discord.Embed(
            title="🏆 Wordle Wins Leaderboard",
            color=discord.Color.gold(),
            description=f"Top {len(data)} players by total wins"
        )

        medals = ['🥇', '🥈', '🥉']

        for i, (player, wins) in enumerate(data, 1):
            medal = medals[i-1] if i <= 3 else f"{i}."
            embed.add_field(
                name=f"{medal} {player}",
                value=f"**{wins}** wins",
                inline=False
            )

        await ctx.send(embed=embed)

    @bot.command(name='stats', aliases=['mystats', 'profile'])
    async def stats(ctx, player: Optional[str] = None):
        """
        Show personal stats for a player

        Usage: !stats [@user]
        Example: !stats @Soham_c.7
        """
        # If no player specified, use the command invoker
        if player is None:
            player_name = ctx.author.name
        else:
            # Clean up the player name
            player_name = player.lstrip('@')

        stats_data = database.get_player_stats(player_name)

        if not stats_data:
            await ctx.send(f"No stats found for **{player_name}**. Have they played any Wordle?")
            return

        embed = discord.Embed(
            title=f"📊 Stats for {player_name}",
            color=discord.Color.blue()
        )

        embed.add_field(name="Total Games", value=str(stats_data['total_games']), inline=True)
        embed.add_field(name="Total Wins", value=str(stats_data['total_wins']), inline=True)
        embed.add_field(
            name="Win Rate",
            value=f"{stats_data['win_rate']:.1f}%",
            inline=True
        )

        if stats_data['avg_score']:
            embed.add_field(
                name="Average Score",
                value=f"{stats_data['avg_score']:.2f}",
                inline=True
            )

        if stats_data['best_score']:
            embed.add_field(name="Best Score", value=f"{stats_data['best_score']}/6", inline=True)

        embed.add_field(
            name="Fails",
            value=f"{stats_data['fail_count']} ({stats_data['fail_rate']:.1f}%)",
            inline=True
        )

        # Score distribution
        dist_str = []
        for score in range(1, 8):
            count = stats_data['score_distribution'].get(score, 0)
            if count > 0:
                label = 'X' if score == 7 else str(score)
                dist_str.append(f"{label}/6: {count}")

        if dist_str:
            embed.add_field(
                name="Score Distribution",
                value="\n".join(dist_str),
                inline=False
            )

        await ctx.send(embed=embed)

    @bot.command(name='average', aliases=['averages', 'avg'])
    async def average(ctx):
        """
        Show average scores for all players

        Usage: !average
        """
        data = database.get_all_players_averages()

        if not data:
            await ctx.send("No data available yet!")
            return

        embed = discord.Embed(
            title="📈 Average Scores",
            color=discord.Color.green(),
            description="Lower is better!"
        )

        for player, avg_score, game_count in data[:10]:
            if avg_score is not None:
                embed.add_field(
                    name=player,
                    value=f"{avg_score:.2f} ({game_count} games)",
                    inline=False
                )

        await ctx.send(embed=embed)

    @bot.command(name='streak', aliases=['streaks'])
    async def streak(ctx):
        """
        Show current and best group streaks

        Usage: !streak
        """
        streak_data = database.get_streak_info()

        embed = discord.Embed(
            title="🔥 Streak Information",
            color=discord.Color.orange()
        )

        embed.add_field(
            name="Current Streak",
            value=f"**{streak_data['current_streak']}** days 🔥",
            inline=True
        )

        embed.add_field(
            name="Best Streak",
            value=f"**{streak_data['best_streak']}** days 🏆",
            inline=True
        )

        await ctx.send(embed=embed)

    @bot.command(name='head2head', aliases=['h2h', 'versus', 'vs'])
    async def head2head(ctx, player1: str, player2: str):
        """
        Compare two players head-to-head

        Usage: !head2head @player1 @player2
        Example: !h2h @Soham_c.7 @kashyapwho
        """
        # Clean player names
        p1 = player1.lstrip('@')
        p2 = player2.lstrip('@')

        h2h_data = database.get_head_to_head(p1, p2)

        if not h2h_data:
            await ctx.send(f"Not enough data to compare **{p1}** and **{p2}**")
            return

        embed = discord.Embed(
            title=f"⚔️ {p1} vs {p2}",
            color=discord.Color.purple()
        )

        embed.add_field(
            name="Head-to-Head",
            value=f"{p1}: **{h2h_data['p1_wins']}** wins\n"
                  f"{p2}: **{h2h_data['p2_wins']}** wins\n"
                  f"Ties: **{h2h_data['ties']}**\n"
                  f"Total matchups: {h2h_data['matchups']}",
            inline=False
        )

        p1_stats = h2h_data['p1_stats']
        p2_stats = h2h_data['p2_stats']

        embed.add_field(
            name=f"{p1} Overall",
            value=f"Games: {p1_stats['total_games']}\n"
                  f"Win Rate: {p1_stats['win_rate']:.1f}%\n"
                  f"Avg Score: {p1_stats['avg_score']:.2f}\n"
                  f"Fail Rate: {p1_stats['fail_rate']:.1f}%",
            inline=True
        )

        embed.add_field(
            name=f"{p2} Overall",
            value=f"Games: {p2_stats['total_games']}\n"
                  f"Win Rate: {p2_stats['win_rate']:.1f}%\n"
                  f"Avg Score: {p2_stats['avg_score']:.2f}\n"
                  f"Fail Rate: {p2_stats['fail_rate']:.1f}%",
            inline=True
        )

        await ctx.send(embed=embed)

    @bot.command(name='luck', aliases=['lucky', 'luckiest'])
    async def luck(ctx, limit: int = 10):
        """
        Show who gets the most lucky scores (1/6 and 2/6)

        Usage: !luck [limit]
        Example: !luck 5
        """
        data = database.get_lucky_players()

        if not data:
            await ctx.send("No lucky scores yet!")
            return

        embed = discord.Embed(
            title="🍀 Luckiest Players",
            color=discord.Color.gold(),
            description="Most 1/6 and 2/6 scores"
        )

        for i, (player, count) in enumerate(data[:limit], 1):
            emoji = '🍀' if i == 1 else '✨' if i <= 3 else '⭐'
            embed.add_field(
                name=f"{i}. {emoji} {player}",
                value=f"**{count}** lucky scores",
                inline=False
            )

        await ctx.send(embed=embed)

    @bot.command(name='whowins', aliases=['weekday', 'dayofweek'])
    async def whowins(ctx):
        """
        Show who wins most on each weekday

        Usage: !whowins
        """
        weekday_data = database.get_weekday_winners()

        if not weekday_data:
            await ctx.send("Not enough data yet!")
            return

        embed = discord.Embed(
            title="📅 Weekday Winners",
            color=discord.Color.teal(),
            description="Who dominates each day of the week"
        )

        for weekday, (player, wins) in weekday_data.items():
            embed.add_field(
                name=weekday,
                value=f"**{player}** ({wins} wins)",
                inline=True
            )

        await ctx.send(embed=embed)

    @bot.command(name='chart', aliases=['graph', 'viz'])
    async def chart(ctx, chart_type: str = 'leaderboard'):
        """
        Generate visualizations

        Usage: !chart [type]
        Types: leaderboard, average, luck, participation
        Example: !chart leaderboard
        """
        chart_type = chart_type.lower()

        try:
            if chart_type in ['leaderboard', 'wins', 'lb']:
                chart_buf = visualizations.create_wins_leaderboard_chart()
                title = "Wins Leaderboard"

            elif chart_type in ['average', 'avg', 'averages']:
                chart_buf = visualizations.create_average_scores_chart()
                title = "Average Scores"

            elif chart_type in ['luck', 'lucky']:
                chart_buf = visualizations.create_luck_chart()
                title = "Luckiest Players"

            elif chart_type in ['participation', 'part', 'days']:
                chart_buf = visualizations.create_participation_chart()
                title = "Participation Rate"

            else:
                await ctx.send(
                    f"Unknown chart type: **{chart_type}**\n"
                    "Available types: `leaderboard`, `average`, `luck`, `participation`"
                )
                return

            file = discord.File(chart_buf, filename=f'{chart_type}_chart.png')
            await ctx.send(f"📊 **{title}**", file=file)

        except Exception as e:
            await ctx.send(f"Error generating chart: {str(e)}")

    @bot.command(name='chartdist', aliases=['distribution', 'dist'])
    async def chart_distribution(ctx, player: Optional[str] = None):
        """
        Generate score distribution chart for a player

        Usage: !chartdist [@player]
        Example: !chartdist @Soham_c.7
        """
        # If no player specified, use the command invoker
        if player is None:
            player_name = ctx.author.name
        else:
            player_name = player.lstrip('@')

        try:
            chart_buf = visualizations.create_score_distribution_chart(player_name)
            file = discord.File(chart_buf, filename=f'{player_name}_distribution.png')
            await ctx.send(f"📊 **Score Distribution for {player_name}**", file=file)

        except Exception as e:
            await ctx.send(f"Error generating chart: {str(e)}")

    @bot.command(name='charth2h', aliases=['h2hchart', 'vschart'])
    async def chart_head2head(ctx, player1: str, player2: str):
        """
        Generate head-to-head comparison chart

        Usage: !charth2h @player1 @player2
        Example: !charth2h @Soham_c.7 @kashyapwho
        """
        p1 = player1.lstrip('@')
        p2 = player2.lstrip('@')

        try:
            chart_buf = visualizations.create_head_to_head_chart(p1, p2)
            file = discord.File(chart_buf, filename=f'{p1}_vs_{p2}.png')
            await ctx.send(f"⚔️ **{p1} vs {p2}**", file=file)

        except Exception as e:
            await ctx.send(f"Error generating chart: {str(e)}")

    @bot.command(name='history', aliases=['recent', 'last'])
    async def history(ctx, days: int = 7):
        """
        Show recent results

        Usage: !history [days]
        Example: !history 5
        """
        results = database.get_recent_results(days)

        if not results:
            await ctx.send("No recent results found!")
            return

        # Group by date
        from collections import defaultdict
        by_date = defaultdict(list)

        for result in results:
            by_date[result['date']].append(result)

        embed = discord.Embed(
            title=f"📜 Last {min(days, len(by_date))} Days",
            color=discord.Color.blue()
        )

        # Show most recent days first
        for date in sorted(by_date.keys(), reverse=True)[:days]:
            day_results = by_date[date]

            # Sort by score
            day_results.sort(key=lambda x: x['score'])

            result_lines = []
            for r in day_results:
                score_str = 'X' if r['score'] == 7 else str(r['score'])
                winner_mark = '👑 ' if r['is_winner'] else ''
                result_lines.append(f"{winner_mark}{r['player_name']}: {score_str}/6")

            embed.add_field(
                name=date,
                value="\n".join(result_lines) or "No data",
                inline=False
            )

        await ctx.send(embed=embed)

    @bot.command(name='help_wordle', aliases=['commands', 'cmdlist'])
    async def help_wordle(ctx):
        """
        Show all available commands

        Usage: !help_wordle
        """
        embed = discord.Embed(
            title="🤖 Wordle Stats Bot Commands",
            color=discord.Color.blue(),
            description="Track and analyze your group's Wordle performance"
        )

        commands_list = [
            ("!leaderboard [limit]", "Show wins leaderboard"),
            ("!stats [@player]", "Show personal stats"),
            ("!average", "Show average scores"),
            ("!streak", "Show group streaks"),
            ("!head2head @p1 @p2", "Compare two players"),
            ("!luck [limit]", "Show luckiest players (1/6, 2/6)"),
            ("!whowins", "Show weekday winners"),
            ("!history [days]", "Show recent results"),
            ("!chart [type]", "Generate charts (types: leaderboard, average, luck, participation)"),
            ("!chartdist [@player]", "Score distribution chart"),
            ("!charth2h @p1 @p2", "Head-to-head chart"),
        ]

        for cmd, desc in commands_list:
            embed.add_field(name=cmd, value=desc, inline=False)

        embed.set_footer(text="Built by Soham and Claude 🤖")

        await ctx.send(embed=embed)
