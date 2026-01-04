"""
Message parsing logic for Wordle bot results    
"""

import re
from datetime import datetime, timedelta
from typing import List, Tuple, Optional
from config import CROWN_EMOJI, SCORE_PATTERN, STREAK_PATTERN, FAIL_SCORE

class WordleResult:
    """
    Represents a Wordle game result.
    """
    
    def __init__(self, player_name: str, score: int, is_winner: bool):
        self.player_name = player_name
        self.score = score
        self.is_winner = is_winner


    def __repr__(self):
        winner_mark = "👑" if self.is_winner else ""
        return f"{winner_mark}{self.player_name}: {self.score}/6"

def extract_streak(message : str) -> Optional[int]:
    match = re.search(STREAK_PATTERN, message)
    if match:
        return int(match.group(1))
    return None


def extract_wordle_number(message: str) -> Optional[int]:
    """
    Extract the Wordle puzzle number if present

    Args:
        message: The message content

    Returns:
        Wordle number or None if not found
    """
    # Pattern: "Wordle 1234" or "#1234"
    patterns = [
        r'Wordle\s+(\d+)',
        r'#(\d+)',
        r'puzzle\s+(\d+)'
    ]

    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None


def clean_player_name(name: str) -> str:
    """
    Clean a player name by removing @ symbol and extra whitespace

    Args:
        name: Raw player name (e.g., "@username")

    Returns:
        Cleaned player name (e.g., "username")
    """
    return name.strip().lstrip('@')


def parse_score_line(line: str) -> List[WordleResult]:
    """
    Parse a single score line from the message

    Examples:
        "👑 3/6: @Soham_c.7" -> [WordleResult("Soham_c.7", 3, True)]
        "4/6: @kashyapwho @Santhosh" -> [WordleResult("kashyapwho", 4, False), ...]
        "X/6: @player" -> [WordleResult("player", 7, False)]

    Args:
        line: A single line containing scores

    Returns:
        List of WordleResult objects
    """
    results = []

    # Check if this line has a crown (winner)
    is_winner = CROWN_EMOJI in line

    # Extract score (N/6 or X/6)
    score_match = re.search(r'([X\d])/6', line)
    if not score_match:
        return results

    score_str = score_match.group(1)
    score = FAIL_SCORE if score_str == 'X' else int(score_str)

    # Extract all player names after the score
    # Pattern: @username (can have letters, numbers, dots, underscores)
    player_matches = re.findall(r'@([\w.]+)', line)

    for player_name in player_matches:
        results.append(WordleResult(
            player_name=clean_player_name(player_name),
            score=score,
            is_winner=is_winner
        ))

    return results


def parse_wordle_message(message: str) -> Tuple[List[WordleResult], Optional[int], Optional[int]]:
    """
    Parse a complete Wordle bot message

    Handles multiple formats:
    - Multi-line format
    - Single-line format
    - Tied winners

    Args:
        message: The full message content from the Wordle bot

    Returns:
        Tuple of (results_list, streak_number, wordle_number)
    """
    # Check if this is a valid Wordle results message
    if 'streak' not in message.lower() and 'results' not in message.lower():
        return [], None, None

    results = []
    streak = extract_streak(message)
    wordle_number = extract_wordle_number(message)

    # Split message into lines and process each
    lines = message.split('\n')

    for line in lines:
        # Skip lines that don't contain scores
        if '/6' not in line:
            continue

        line_results = parse_score_line(line)
        results.extend(line_results)

    # If multi-line didn't work, try parsing as single line
    # This handles: "4/6: @user1 5/6: @user2 X/6: @user3"
    if not results and '/6' in message:
        # Split by score patterns
        score_segments = re.split(r'(?=[👑]?\s*[X\d]/6:)', message)

        for segment in score_segments:
            if '/6' in segment:
                segment_results = parse_score_line(segment)
                results.extend(segment_results)

    return results, streak, wordle_number


def get_date_from_timestamp(timestamp: datetime, is_yesterday: bool = True) -> str:
    """
    Get the date string for a result

    Args:
        timestamp: Message timestamp
        is_yesterday: Whether the results are for "yesterday"

    Returns:
        Date string in YYYY-MM-DD format
    """
    date = timestamp - timedelta(days=1) if is_yesterday else timestamp
    return date.strftime('%Y-%m-%d')


def validate_results(results: List[WordleResult]) -> bool:
    """
    Validate parsed results

    Args:
        results: List of WordleResult objects

    Returns:
        True if results are valid
    """
    if not results:
        return False

    # Check that at least one player has a valid score
    valid_scores = [r for r in results if 1 <= r.score <= FAIL_SCORE]
    if not valid_scores:
        return False

    # Check that all player names are non-empty
    if any(not r.player_name for r in results):
        return False

    return True


# Test function for debugging
def test_parser():
    """Test the parser with sample messages"""

    test_messages = [
        # Multi-line format
        """Your group is on a 95 day streak! 🔥🔥🔥 Here are yesterday's results:
👑 3/6: @Soham_c.7
4/6: @kashyapwho @Santhosh""",

        # Single-line format
        "Your group is on a 95 day streak! Here are yesterday's results: 👑 4/6: @Santhosh 6/6: @Soham_c.7 X/6: @kashyapwho",

        # Tied winners
        """Your group is on a 100 day streak! Here are yesterday's results:
👑 3/6: @Soham_c.7 @kashyapwho
4/6: @Santhosh""",
    ]

    print("=== Parser Tests ===\n")

    for i, msg in enumerate(test_messages, 1):
        print(f"Test {i}:")
        print(f"Message: {msg[:80]}...")
        results, streak, wordle_num = parse_wordle_message(msg)
        print(f"Streak: {streak}")
        print(f"Results:")
        for r in results:
            print(f"  - {r}")
        print(f"Valid: {validate_results(results)}\n")


if __name__ == "__main__":
    test_parser()