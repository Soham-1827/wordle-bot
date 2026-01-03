"""
Database operations for the Wordle Discord Stats Bot
"""
import sqlite3
from datetime import datetime
from typing import List, Tuple, Optional
from config import DATABASE_PATH


def init_database():
    """Initialize the SQLite database with the required schema"""
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            wordle_number INTEGER,
            player_name TEXT NOT NULL,
            player_id TEXT,
            score INTEGER NOT NULL,
            is_winner BOOLEAN DEFAULT FALSE,
            streak_day INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(date, player_name)
        )
    ''')

    # Create indexes for better query performance
    c.execute('CREATE INDEX IF NOT EXISTS idx_date ON results(date)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_player_name ON results(player_name)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_is_winner ON results(is_winner)')

    conn.commit()
    conn.close()
    print(f"✅ Database initialized at {DATABASE_PATH}")


def save_result(date: str, player_name: str, score: int, is_winner: bool,
                streak_day: int, player_id: Optional[str] = None,
                wordle_number: Optional[int] = None) -> bool:
    """
    Save a single Wordle result to the database

    Args:
        date: Date in YYYY-MM-DD format
        player_name: Discord username
        score: Score (1-6 for success, 7 for X/6 fail)
        is_winner: Whether this player won that day
        streak_day: Group streak count
        player_id: Discord user ID (optional)
        wordle_number: Wordle puzzle number (optional)

    Returns:
        True if saved successfully, False if duplicate
    """
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()

    try:
        c.execute('''
            INSERT INTO results (date, player_name, score, is_winner, streak_day, player_id, wordle_number)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (date, player_name, score, is_winner, streak_day, player_id, wordle_number))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        # Duplicate entry (same player, same date)
        conn.close()
        return False


def get_leaderboard(limit: int = 10) -> List[Tuple[str, int]]:
    """
    Get the wins leaderboard

    Returns:
        List of (player_name, win_count) tuples
    """
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()

    c.execute('''
        SELECT player_name, COUNT(*) as wins
        FROM results
        WHERE is_winner = TRUE
        GROUP BY player_name
        ORDER BY wins DESC
        LIMIT ?
    ''', (limit,))

    results = c.fetchall()
    conn.close()
    return results


def get_player_stats(player_name: str) -> dict:
    """
    Get comprehensive stats for a single player

    Returns:
        Dictionary with various stats
    """
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()

    # Total games
    c.execute('SELECT COUNT(*) FROM results WHERE player_name = ?', (player_name,))
    total_games = c.fetchone()[0]

    if total_games == 0:
        conn.close()
        return None

    # Total wins
    c.execute('SELECT COUNT(*) FROM results WHERE player_name = ? AND is_winner = TRUE',
              (player_name,))
    total_wins = c.fetchone()[0]

    # Average score (excluding fails)
    c.execute('''
        SELECT AVG(score)
        FROM results
        WHERE player_name = ? AND score < 7
    ''', (player_name,))
    avg_score = c.fetchone()[0]

    # Fail count
    c.execute('SELECT COUNT(*) FROM results WHERE player_name = ? AND score = 7',
              (player_name,))
    fail_count = c.fetchone()[0]

    # Score distribution
    c.execute('''
        SELECT score, COUNT(*) as count
        FROM results
        WHERE player_name = ?
        GROUP BY score
        ORDER BY score
    ''', (player_name,))
    score_distribution = {row[0]: row[1] for row in c.fetchall()}

    # Best score
    c.execute('SELECT MIN(score) FROM results WHERE player_name = ?', (player_name,))
    best_score = c.fetchone()[0]

    conn.close()

    return {
        'player_name': player_name,
        'total_games': total_games,
        'total_wins': total_wins,
        'win_rate': (total_wins / total_games * 100) if total_games > 0 else 0,
        'avg_score': round(avg_score, 2) if avg_score else None,
        'fail_count': fail_count,
        'fail_rate': (fail_count / total_games * 100) if total_games > 0 else 0,
        'score_distribution': score_distribution,
        'best_score': best_score if best_score < 7 else None
    }


def get_all_players_averages() -> List[Tuple[str, float, int]]:
    """
    Get average scores for all players

    Returns:
        List of (player_name, avg_score, game_count) tuples
    """
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()

    c.execute('''
        SELECT
            player_name,
            AVG(CASE WHEN score < 7 THEN score ELSE NULL END) as avg_score,
            COUNT(*) as game_count
        FROM results
        GROUP BY player_name
        ORDER BY avg_score ASC
    ''')

    results = c.fetchall()
    conn.close()
    return results


def get_recent_results(days: int = 7) -> List[dict]:
    """
    Get results from the last N days

    Returns:
        List of result dictionaries
    """
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute('''
        SELECT * FROM results
        ORDER BY date DESC
        LIMIT ?
    ''', (days * 10,))  # Assume ~10 players per day max

    results = [dict(row) for row in c.fetchall()]
    conn.close()
    return results


def get_head_to_head(player1: str, player2: str) -> dict:
    """
    Compare two players head-to-head

    Returns:
        Dictionary with comparison stats
    """
    p1_stats = get_player_stats(player1)
    p2_stats = get_player_stats(player2)

    if not p1_stats or not p2_stats:
        return None

    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()

    # Get days where both played
    c.execute('''
        SELECT
            r1.date,
            r1.score as p1_score,
            r2.score as p2_score
        FROM results r1
        INNER JOIN results r2 ON r1.date = r2.date
        WHERE r1.player_name = ? AND r2.player_name = ?
        ORDER BY r1.date DESC
    ''', (player1, player2))

    matchups = c.fetchall()
    conn.close()

    p1_wins = sum(1 for _, p1_score, p2_score in matchups if p1_score < p2_score)
    p2_wins = sum(1 for _, p1_score, p2_score in matchups if p2_score < p1_score)
    ties = sum(1 for _, p1_score, p2_score in matchups if p1_score == p2_score)

    return {
        'player1': player1,
        'player2': player2,
        'p1_stats': p1_stats,
        'p2_stats': p2_stats,
        'matchups': len(matchups),
        'p1_wins': p1_wins,
        'p2_wins': p2_wins,
        'ties': ties
    }


def get_streak_info() -> dict:
    """
    Get current and best streak information

    Returns:
        Dictionary with streak stats
    """
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()

    # Get most recent streak
    c.execute('SELECT streak_day FROM results ORDER BY date DESC LIMIT 1')
    result = c.fetchone()
    current_streak = result[0] if result else 0

    # Get best streak ever
    c.execute('SELECT MAX(streak_day) FROM results')
    best_streak = c.fetchone()[0] or 0

    conn.close()

    return {
        'current_streak': current_streak,
        'best_streak': best_streak
    }


def get_lucky_players() -> List[Tuple[str, int]]:
    """
    Get players with most 1/6 and 2/6 scores

    Returns:
        List of (player_name, lucky_count) tuples
    """
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()

    c.execute('''
        SELECT player_name, COUNT(*) as lucky_count
        FROM results
        WHERE score IN (1, 2)
        GROUP BY player_name
        ORDER BY lucky_count DESC
    ''')

    results = c.fetchall()
    conn.close()
    return results


def get_weekday_winners() -> dict:
    """
    Get who wins most on each weekday

    Returns:
        Dictionary mapping weekday to (player_name, win_count)
    """
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()

    weekday_stats = {}
    weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

    for i, weekday in enumerate(weekdays):
        c.execute('''
            SELECT player_name, COUNT(*) as wins
            FROM results
            WHERE is_winner = TRUE
            AND CAST(strftime('%w', date) AS INTEGER) = ?
            GROUP BY player_name
            ORDER BY wins DESC
            LIMIT 1
        ''', (i,))

        result = c.fetchone()
        if result:
            weekday_stats[weekday] = result

    conn.close()
    return weekday_stats


# Initialize database on module import
init_database()
