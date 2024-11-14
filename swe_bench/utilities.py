"""
Utility functions.
"""

import requests

from swe_bench.models import Split


def get_all_entries(split: Split, timeout: int = 100) -> list[str]:
    """
    Get the list of all leaderboard entries for a given split.
    """

    results: list[str] = []

    url = f"https://api.github.com/repos/swe-bench/experiments/contents/evaluation/{split.value}"
    request = requests.get(url, timeout=timeout)

    match request.status_code:
        case 200:
            for entry in request.json():
                if entry["type"] == "dir":
                    results.append(entry["name"])

        case 408:
            raise ValueError(f"Request timed out after {timeout} seconds.")

        case _:
            raise ValueError(f"Unknown status code {request.status_code}.")

    return results
