"""
Chart generation for Wordle stats
"""
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for Discord bot
import io
from typing import List, Tuple, Optional
import database


def create_wins_leaderboard_chart(limit: int = 10) -> io.BytesIO:
    """
    Create a horizontal bar chart showing wins leaderboard

    Args:
        limit: Number of top players to show

    Returns:
        BytesIO object containing the chart image
    """
    data = database.get_leaderboard(limit)

    if not data:
        # Create empty chart
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, 'No data available yet', ha='center', va='center', fontsize=14)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
    else:
        players = [row[0] for row in data]
        wins = [row[1] for row in data]

        # Create horizontal bar chart
        fig, ax = plt.subplots(figsize=(10, max(6, len(players) * 0.5)))
        colors = plt.cm.viridis([i / len(players) for i in range(len(players))])
        bars = ax.barh(players, wins, color=colors)

        # Add value labels on bars
        for i, (bar, win_count) in enumerate(zip(bars, wins)):
            width = bar.get_width()
            ax.text(width, bar.get_y() + bar.get_height()/2,
                   f' {win_count}',
                   ha='left', va='center', fontweight='bold')

        # Add medals for top 3
        medals = ['🥇', '🥈', '🥉']
        for i in range(min(3, len(players))):
            ax.text(-0.5, i, medals[i], ha='right', va='center', fontsize=16)

        ax.set_xlabel('Total Wins', fontsize=12, fontweight='bold')
        ax.set_title('Wordle Wins Leaderboard', fontsize=16, fontweight='bold', pad=20)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        plt.tight_layout()

    # Save to BytesIO
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)

    return buf


def create_participation_chart() -> io.BytesIO:
    """
    Create a chart showing how many days each player has participated

    Returns:
        BytesIO object containing the chart image
    """
    # Get participation data from database
    import sqlite3
    conn = sqlite3.connect(database.DATABASE_PATH)
    c = conn.cursor()

    c.execute('''
        SELECT player_name, COUNT(DISTINCT date) as days_played
        FROM results
        GROUP BY player_name
        ORDER BY days_played DESC
    ''')

    data = c.fetchall()
    conn.close()

    if not data:
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, 'No data available yet', ha='center', va='center', fontsize=14)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
    else:
        players = [row[0] for row in data]
        days_played = [row[1] for row in data]

        # Get total possible days (from earliest to latest date in database)
        conn = sqlite3.connect(database.DATABASE_PATH)
        c = conn.cursor()
        c.execute('SELECT MIN(date), MAX(date) FROM results')
        min_date, max_date = c.fetchone()
        conn.close()

        if min_date and max_date:
            from datetime import datetime
            start = datetime.strptime(min_date, '%Y-%m-%d')
            end = datetime.strptime(max_date, '%Y-%m-%d')
            total_days = (end - start).days + 1
        else:
            total_days = max(days_played) if days_played else 0

        # Create horizontal bar chart
        fig, ax = plt.subplots(figsize=(10, max(6, len(players) * 0.5)))

        # Color based on participation rate
        participation_rates = [d / total_days for d in days_played]
        colors = plt.cm.RdYlGn([rate for rate in participation_rates])
        bars = ax.barh(players, days_played, color=colors)

        # Add value labels with participation percentage
        for bar, days, rate in zip(bars, days_played, participation_rates):
            width = bar.get_width()
            ax.text(width, bar.get_y() + bar.get_height()/2,
                   f' {days}/{total_days} ({rate*100:.1f}%)',
                   ha='left', va='center', fontsize=9, fontweight='bold')

        ax.set_xlabel('Days Played', fontsize=12, fontweight='bold')
        ax.set_title(f'Participation Rate (Total: {total_days} days)',
                    fontsize=16, fontweight='bold', pad=20)
        ax.set_xlim(0, total_days * 1.15)  # Add some padding for labels
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)

    return buf


def create_average_scores_chart() -> io.BytesIO:
    """
    Create a bar chart comparing average scores

    Returns:
        BytesIO object containing the chart image
    """
    data = database.get_all_players_averages()

    if not data:
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, 'No data available yet', ha='center', va='center', fontsize=14)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
    else:
        players = [row[0] for row in data if row[1] is not None]
        averages = [row[1] for row in data if row[1] is not None]
        game_counts = [row[2] for row in data if row[1] is not None]

        # Create bar chart
        fig, ax = plt.subplots(figsize=(10, max(6, len(players) * 0.5)))

        # Color bars based on average (lower is better, so reverse colors)
        colors = plt.cm.RdYlGn_r([i / len(players) for i in range(len(players))])
        bars = ax.barh(players, averages, color=colors)

        # Add value labels
        for bar, avg, games in zip(bars, averages, game_counts):
            width = bar.get_width()
            ax.text(width, bar.get_y() + bar.get_height()/2,
                   f' {avg:.2f} ({games} games)',
                   ha='left', va='center', fontsize=9)

        ax.set_xlabel('Average Score (lower is better)', fontsize=12, fontweight='bold')
        ax.set_title('Average Wordle Scores', fontsize=16, fontweight='bold', pad=20)
        ax.set_xlim(0, max(averages) * 1.2 if averages else 6)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)

    return buf


def create_score_distribution_chart(player_name: str) -> io.BytesIO:
    """
    Create a stacked bar chart showing score distribution for a player

    Args:
        player_name: Name of the player

    Returns:
        BytesIO object containing the chart image
    """
    stats = database.get_player_stats(player_name)

    if not stats or not stats['score_distribution']:
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, f'No data available for {player_name}',
               ha='center', va='center', fontsize=14)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
    else:
        dist = stats['score_distribution']

        # Prepare data
        scores = []
        counts = []
        labels = []

        for score in range(1, 8):  # 1-6 and 7 (fail)
            count = dist.get(score, 0)
            if count > 0:
                scores.append(score)
                counts.append(count)
                labels.append('X' if score == 7 else str(score))

        # Create bar chart
        fig, ax = plt.subplots(figsize=(10, 6))
        colors = ['#538d4e', '#6aaa64', '#b59f3b', '#c9b458', '#edcc61', '#f5793a', '#d73027']
        bars = ax.bar(labels, counts, color=[colors[s-1] for s in scores])

        # Add value labels
        for bar, count in zip(bars, counts):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, height,
                   f'{count}\n({count/stats["total_games"]*100:.1f}%)',
                   ha='center', va='bottom', fontsize=10)

        ax.set_xlabel('Score', fontsize=12, fontweight='bold')
        ax.set_ylabel('Count', fontsize=12, fontweight='bold')
        ax.set_title(f'Score Distribution for {player_name}',
                    fontsize=16, fontweight='bold', pad=20)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)

    return buf


def create_head_to_head_chart(player1: str, player2: str) -> io.BytesIO:
    """
    Create a comparison chart for two players

    Args:
        player1: First player name
        player2: Second player name

    Returns:
        BytesIO object containing the chart image
    """
    h2h = database.get_head_to_head(player1, player2)

    if not h2h:
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, 'Not enough data for comparison',
               ha='center', va='center', fontsize=14)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
    else:
        # Create figure with subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

        # Left plot: Win comparison in head-to-head matchups
        matchup_labels = [player1, 'Ties', player2]
        matchup_values = [h2h['p1_wins'], h2h['ties'], h2h['p2_wins']]
        colors = ['#2ecc71', '#95a5a6', '#e74c3c']

        ax1.bar(matchup_labels, matchup_values, color=colors)
        ax1.set_ylabel('Count', fontsize=12, fontweight='bold')
        ax1.set_title(f'Head-to-Head Matchups ({h2h["matchups"]} games)',
                     fontsize=14, fontweight='bold')

        for i, v in enumerate(matchup_values):
            ax1.text(i, v, str(v), ha='center', va='bottom', fontweight='bold')

        # Right plot: Overall stats comparison
        stats_labels = ['Win Rate %', 'Avg Score', 'Fail Rate %']
        p1_stats_values = [
            h2h['p1_stats']['win_rate'],
            h2h['p1_stats']['avg_score'] or 0,
            h2h['p1_stats']['fail_rate']
        ]
        p2_stats_values = [
            h2h['p2_stats']['win_rate'],
            h2h['p2_stats']['avg_score'] or 0,
            h2h['p2_stats']['fail_rate']
        ]

        x = range(len(stats_labels))
        width = 0.35

        ax2.bar([i - width/2 for i in x], p1_stats_values, width,
               label=player1, color='#3498db')
        ax2.bar([i + width/2 for i in x], p2_stats_values, width,
               label=player2, color='#e74c3c')

        ax2.set_ylabel('Value', fontsize=12, fontweight='bold')
        ax2.set_title('Overall Stats Comparison', fontsize=14, fontweight='bold')
        ax2.set_xticks(x)
        ax2.set_xticklabels(stats_labels)
        ax2.legend()

        # Note: Lower average score is better, add annotation
        ax2.text(1, max(p1_stats_values[1], p2_stats_values[1]) * 1.1,
                '(lower is better)', ha='center', fontsize=9, style='italic')

        for spine in ['top', 'right']:
            ax1.spines[spine].set_visible(False)
            ax2.spines[spine].set_visible(False)

        plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)

    return buf


def create_luck_chart(limit: int = 10) -> io.BytesIO:
    """
    Create a chart showing who gets the most lucky scores (1/6 and 2/6)

    Args:
        limit: Number of top players to show

    Returns:
        BytesIO object containing the chart image
    """
    data = database.get_lucky_players()

    if not data:
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, 'No lucky scores yet!', ha='center', va='center', fontsize=14)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
    else:
        players = [row[0] for row in data[:limit]]
        lucky_counts = [row[1] for row in data[:limit]]

        # Create bar chart
        fig, ax = plt.subplots(figsize=(10, max(6, len(players) * 0.5)))
        colors = plt.cm.YlOrRd([i / len(players) for i in range(len(players))])
        bars = ax.barh(players, lucky_counts, color=colors)

        # Add value labels
        for bar, count in zip(bars, lucky_counts):
            width = bar.get_width()
            ax.text(width, bar.get_y() + bar.get_height()/2,
                   f' {count}',
                   ha='left', va='center', fontweight='bold')

        # Add trophy for top player
        if players:
            ax.text(-0.5, 0, '🍀', ha='right', va='center', fontsize=20)

        ax.set_xlabel('Lucky Scores (1/6 or 2/6)', fontsize=12, fontweight='bold')
        ax.set_title('Luckiest Players', fontsize=16, fontweight='bold', pad=20)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)

    return buf
