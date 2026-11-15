"""
Song scoring and ranking for the Music Recommender Simulation.

The dictionary-based functions (load_songs, score_song, recommend_songs) hold
the real logic. The Song / UserProfile / Recommender classes convert their data
to dictionaries and call those same functions, so there is only one scoring
implementation.
"""

import csv
from dataclasses import asdict, dataclass
from typing import Dict, List, Tuple

# Points for each part of the score (see README "Scoring: the starting recipe").
GENRE_POINTS = 3.0
MOOD_POINTS = 2.0
ENERGY_POINTS = 2.0
ACOUSTIC_POINTS = 1.0
MAX_SCORE = GENRE_POINTS + MOOD_POINTS + ENERGY_POINTS + ACOUSTIC_POINTS  # 8.0

# Scores are rounded to this many decimal places before ranking, so tiny
# floating-point differences (2.68 vs 2.6799999999999997) count as ties.
RANKING_DECIMALS = 4

# CSV columns, in file order, and the numeric ones that need converting.
FLOAT_FIELDS = ("energy", "tempo_bpm", "valence", "danceability", "acousticness")
CSV_FIELDS = ("id", "title", "artist", "genre", "mood") + FLOAT_FIELDS

# Keys score_song() needs from the preferences and from each song.
PREF_KEYS = ("favorite_genre", "favorite_mood", "target_energy", "likes_acoustic")
SONG_SCORING_KEYS = ("genre", "mood", "energy", "acousticness")


@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float


@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool


class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py

    Converts Song and UserProfile objects to dictionaries and reuses the same
    scoring and ranking code as score_song() and recommend_songs().
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """Return the top k Song objects for this user, best match first."""
        song_dicts = [asdict(song) for song in self.songs]
        ranked = _rank(asdict(user), song_dicts, k)
        return [self.songs[position] for position, _score, _reasons in ranked]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Explain one song's score for this user using the real scoring reasons."""
        score, reasons = score_song(asdict(user), asdict(song))
        return f"Score {score:.2f} / {MAX_SCORE:g}: " + "; ".join(reasons)


def load_songs(csv_path: str) -> List[Dict]:
    """
    Loads songs from a CSV file.
    Required by src/main.py

    Returns one dictionary per row. "id" becomes an int; energy, tempo_bpm,
    valence, danceability and acousticness become floats. Raises ValueError
    if a column is missing or a value can't be read as a number.
    """
    songs = []
    with open(csv_path, newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        missing = [name for name in CSV_FIELDS if name not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"{csv_path} is missing column(s): {', '.join(missing)}")

        for row in reader:
            where = f"{csv_path}, line {reader.line_num}"
            if None in row:
                raise ValueError(f"{where}: has more values than there are columns")
            song = dict(row)
            song["id"] = _parse_number(row, "id", int, where)
            for field in FLOAT_FIELDS:
                song[field] = _parse_number(row, field, float, where)
            songs.append(song)
    return songs


def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """
    Scores a single song against user preferences.
    Required by recommend_songs() and src/main.py

    Returns (score, reasons). score is the unrounded total, from 0 to 8.
    reasons lists what every part added, e.g. "genre match: pop (+3.00)".
    Raises ValueError or TypeError if a needed value is missing or invalid.
    """
    _check_prefs(user_prefs)
    _require_keys(song, SONG_SCORING_KEYS, "song")
    energy = _unit_number(song["energy"], "song energy")
    acousticness = _unit_number(song["acousticness"], "song acousticness")
    target = float(user_prefs["target_energy"])

    genre_points, genre_reason = _match_points(
        "genre", song["genre"], user_prefs["favorite_genre"], GENRE_POINTS)
    mood_points, mood_reason = _match_points(
        "mood", song["mood"], user_prefs["favorite_mood"], MOOD_POINTS)

    # Closeness, not "more": full points at the target, fewer the further away.
    gap = abs(energy - target)
    energy_points = ENERGY_POINTS * (1 - gap)
    energy_reason = f"energy {energy:.2f} is {gap:.2f} from target {target:.2f} (+{energy_points:.2f})"

    # likes_acoustic=False means "prefers less acoustic", not "no preference".
    if user_prefs["likes_acoustic"]:
        acoustic_points = ACOUSTIC_POINTS * acousticness
        acoustic_reason = f"acousticness {acousticness:.2f}, likes acoustic (+{acoustic_points:.2f})"
    else:
        acoustic_points = ACOUSTIC_POINTS * (1 - acousticness)
        acoustic_reason = f"acousticness {acousticness:.2f}, prefers less acoustic (+{acoustic_points:.2f})"

    score = genre_points + mood_points + energy_points + acoustic_points
    return score, [genre_reason, mood_reason, energy_reason, acoustic_reason]


def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, List[str]]]:
    """
    Functional implementation of the recommendation logic.
    Required by src/main.py

    Returns up to k (song, score, reasons) tuples, best match first. score is
    rounded to 4 decimal places, the same value used for ranking, and songs
    with equal rounded scores keep their input order. An empty song list or
    k=0 gives []; k larger than the catalog returns every song; a negative k
    raises ValueError. The songs list itself is not reordered.
    """
    return [(songs[position], score, reasons) for position, score, reasons in _rank(user_prefs, songs, k)]


def _rank(user_prefs: Dict, songs: List[Dict], k: int) -> List[Tuple[int, float, List[str]]]:
    """
    Score every song and return the top k as (position, rounded score, reasons).

    position is the song's index in the input list. recommend_songs() and
    Recommender.recommend() both use this, so ranking is written only once.
    """
    if isinstance(k, bool) or not isinstance(k, int):
        raise TypeError(f"k must be a whole number, got {k!r}")
    if k < 0:
        raise ValueError(f"k must be 0 or more, got {k}")
    _check_prefs(user_prefs)

    scored = []
    for position, song in enumerate(songs):
        score, reasons = score_song(user_prefs, song)
        scored.append((position, round(score, RANKING_DECIMALS), reasons))

    # sorted() builds a new list; scored.sort() would reorder `scored` in place
    # and return None. Either works here because `scored` is our own list, so the
    # caller's `songs` list is never reordered. Python's sort is stable, even with
    # reverse=True, so equal rounded scores keep their input (CSV) order.
    ranked = sorted(scored, key=lambda item: item[1], reverse=True)
    return ranked[:k]


def _match_points(label: str, song_value, favorite, points: float) -> Tuple[float, str]:
    """Give full points when two genre/mood labels match after trimming and lowercasing."""
    song_label = _clean_label(song_value, f"song {label}")
    favorite_label = _clean_label(favorite, f"favorite_{label}")
    if song_label == favorite_label:
        return points, f"{label} match: {song_label} (+{points:.2f})"
    return 0.0, f"{label} {song_label} does not match {favorite_label} (+0.00)"


def _check_prefs(user_prefs: Dict) -> None:
    """Raise a clear error if user_prefs is missing a key or has an invalid value."""
    _require_keys(user_prefs, PREF_KEYS, "user_prefs")
    _clean_label(user_prefs["favorite_genre"], "favorite_genre")
    _clean_label(user_prefs["favorite_mood"], "favorite_mood")
    _unit_number(user_prefs["target_energy"], "target_energy")
    if not isinstance(user_prefs["likes_acoustic"], bool):
        raise TypeError(f"likes_acoustic must be True or False, got {user_prefs['likes_acoustic']!r}")


def _require_keys(data: Dict, keys: Tuple[str, ...], name: str) -> None:
    """Raise ValueError naming any required keys that data doesn't have."""
    missing = [key for key in keys if key not in data]
    if missing:
        raise ValueError(f"{name} is missing required key(s): {', '.join(missing)}")


def _clean_label(value, name: str) -> str:
    """Trim spaces and lowercase a genre or mood, so " Pop" matches "pop"."""
    if not isinstance(value, str):
        raise TypeError(f"{name} must be text, got {value!r}")
    cleaned = value.strip().lower()
    if not cleaned:
        raise ValueError(f"{name} must not be empty")
    return cleaned


def _unit_number(value, name: str) -> float:
    """Return value as a float, or raise if it isn't a number from 0 to 1."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a number from 0 to 1, got {value!r}")
    if not 0.0 <= value <= 1.0:  # also rejects NaN
        raise ValueError(f"{name} must be from 0 to 1, got {value!r}")
    return float(value)


def _parse_number(row: Dict, field: str, convert, where: str):
    """Convert one CSV value with int or float, with an error naming the line and column."""
    value = row.get(field)
    try:
        return convert(value)
    except (TypeError, ValueError):
        raise ValueError(f"{where}: {field} must be a number, got {value!r}") from None
