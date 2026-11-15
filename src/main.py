"""
Command line runner for the Music Recommender Simulation.

Run from the repository root:

    py -m src.main        (Windows launcher)
    python -m src.main    (if `python` is on your PATH)

It loads data/songs.csv, prints the scoring weights in use, then prints the
top 5 songs, with scores and reasons, for each evaluation profile below.
"""

from pathlib import Path
from typing import Dict, List

from src.recommender import (
    ACOUSTIC_POINTS,
    ENERGY_POINTS,
    GENRE_POINTS,
    MAX_SCORE,
    MOOD_POINTS,
    load_songs,
    recommend_songs,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
SONGS_CSV = REPO_ROOT / "data" / "songs.csv"

# High-Energy Pop is the default profile (the assignment asks for pop/happy).
# target_energy 0.8 is kept from the starter example. likes_acoustic=False is a
# deliberate choice: in this design it means "prefers less acoustic" (not "no
# preference"). That fits the high-energy, mostly electronic pop songs in this
# catalog and matches the profile used in the starter tests.
HIGH_ENERGY_POP = {
    "favorite_genre": "pop",
    "favorite_mood": "happy",
    "target_energy": 0.8,
    "likes_acoustic": False,
}

# Chill Lofi is also the verification example from the README. Expected top
# five: Library Rain 7.86, Midnight Coding 7.57, Focus Flow 5.68,
# Spacewalk Thoughts 4.78, Coffee Shop Stories 2.85.
CHILL_LOFI = {
    "favorite_genre": "lofi",
    "favorite_mood": "chill",
    "target_energy": 0.35,
    "likes_acoustic": True,
}

# Rock has only one song in the catalog, so this tests thin genre coverage.
DEEP_INTENSE_ROCK = {
    "favorite_genre": "rock",
    "favorite_mood": "intense",
    "target_energy": 0.9,
    "likes_acoustic": False,
}

# Adversarial: the genre and mood labels point to the catalog's only sad song,
# which is calm (energy 0.30), while the energy target asks for loud music.
SAD_BUT_HIGH_ENERGY = {
    "favorite_genre": "blues",
    "favorite_mood": "sad",
    "target_energy": 0.9,
    "likes_acoustic": False,
}

# Adversarial: the catalog spells the genre "hip hop". Normalization fixes
# capitalization and outer spaces, but not the hyphen, so this never matches.
HIP_HOP_SPELLING = {
    "favorite_genre": "Hip-Hop",
    "favorite_mood": "confident",
    "target_energy": 0.7,
    "likes_acoustic": False,
}

# Personal-interest profile: the author's confirmed interests are Chinese indie
# and Korean shoegaze, which the catalog doesn't include, so "indie pop" is the
# closest available label. The mood, energy and acoustic values are provisional
# test assumptions, not confirmed preferences.
INDIE_POP_PERSONAL = {
    "favorite_genre": "indie pop",
    "favorite_mood": "moody",
    "target_energy": 0.70,
    "likes_acoustic": False,
}

PROFILES = [
    ("High-Energy Pop (default)", HIGH_ENERGY_POP),
    ("Chill Lofi (verification example)", CHILL_LOFI),
    ("Deep Intense Rock", DEEP_INTENSE_ROCK),
    ("Adversarial: sad mood + high energy", SAD_BUT_HIGH_ENERGY),
    ("Adversarial: 'Hip-Hop' spelling", HIP_HOP_SPELLING),
    ("Personal interest: indie pop (provisional)", INDIE_POP_PERSONAL),
]


def print_recommendations(title: str, user_prefs: Dict, songs: List[Dict], k: int = 5) -> None:
    """Print the full profile, then each top song's title, artist, score and reasons."""
    results = recommend_songs(user_prefs, songs, k)

    print(f"=== {title} ===")
    print("Profile:")
    for key, value in user_prefs.items():
        print(f"  {key}: {value}")

    print(f"\nTop {len(results)} recommendations:")
    for rank, (song, score, reasons) in enumerate(results, start=1):
        # :g prints 8 as "8" and 8.5 as "8.5", so the maximum is always shown exactly.
        print(f"\n{rank}. {song['title']} by {song['artist']}  (score {score:.2f} / {MAX_SCORE:g})")
        for reason in reasons:
            print(f"   - {reason}")
    print()


def main() -> None:
    """Load the catalog and print recommendations for every evaluation profile."""
    songs = load_songs(str(SONGS_CSV))
    print(f"Loaded {len(songs)} songs from {SONGS_CSV.relative_to(REPO_ROOT).as_posix()}")
    print(f"Scoring weights: genre {GENRE_POINTS:g}, mood {MOOD_POINTS:g}, energy {ENERGY_POINTS:g}, "
          f"acoustic {ACOUSTIC_POINTS:g} (max score {MAX_SCORE:g})\n")

    for title, user_prefs in PROFILES:
        print_recommendations(title, user_prefs, songs)


if __name__ == "__main__":
    main()
