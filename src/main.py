"""
Command line runner for the Music Recommender Simulation.

Run from the repository root:

    py -m src.main        (Windows launcher)
    python -m src.main    (if `python` is on your PATH)

It loads data/songs.csv, then prints the top 5 songs, with scores and reasons,
for the default pop/happy profile and for a separate lofi/chill verification
example.
"""

from pathlib import Path
from typing import Dict, List

from src.recommender import MAX_SCORE, load_songs, recommend_songs

REPO_ROOT = Path(__file__).resolve().parent.parent
SONGS_CSV = REPO_ROOT / "data" / "songs.csv"

# Default profile: the assignment asks for pop/happy. target_energy 0.8 is kept
# from the starter example. likes_acoustic=False is a deliberate choice: in this
# design it means "prefers less acoustic" (not "no preference"). That fits the
# high-energy, mostly electronic pop songs in this catalog and matches the
# profile used in the starter tests.
DEFAULT_PREFS = {
    "favorite_genre": "pop",
    "favorite_mood": "happy",
    "target_energy": 0.8,
    "likes_acoustic": False,
}

# Separate verification example from the README. Expected top five:
# Library Rain 7.86, Midnight Coding 7.57, Focus Flow 5.68,
# Spacewalk Thoughts 4.78, Coffee Shop Stories 2.85.
LOFI_VERIFICATION_PREFS = {
    "favorite_genre": "lofi",
    "favorite_mood": "chill",
    "target_energy": 0.35,
    "likes_acoustic": True,
}


def print_recommendations(title: str, user_prefs: Dict, songs: List[Dict], k: int = 5) -> None:
    """Print the full profile, then each top song's title, artist, score and reasons."""
    results = recommend_songs(user_prefs, songs, k)

    print(f"=== {title} ===")
    print("Profile:")
    for key, value in user_prefs.items():
        print(f"  {key}: {value}")

    print(f"\nTop {len(results)} recommendations:")
    for rank, (song, score, reasons) in enumerate(results, start=1):
        print(f"\n{rank}. {song['title']} by {song['artist']}  (score {score:.2f} / {MAX_SCORE:.0f})")
        for reason in reasons:
            print(f"   - {reason}")
    print()


def main() -> None:
    """Load the catalog and print recommendations for both example profiles."""
    songs = load_songs(str(SONGS_CSV))
    print(f"Loaded {len(songs)} songs from {SONGS_CSV.relative_to(REPO_ROOT).as_posix()}\n")

    print_recommendations("Default profile: pop / happy", DEFAULT_PREFS, songs)
    print_recommendations("Verification example: lofi / chill", LOFI_VERIFICATION_PREFS, songs)


if __name__ == "__main__":
    main()
