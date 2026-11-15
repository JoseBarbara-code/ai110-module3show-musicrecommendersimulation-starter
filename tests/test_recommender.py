from pathlib import Path

import pytest

from src.main import main
from src.recommender import (
    Recommender,
    Song,
    UserProfile,
    load_songs,
    recommend_songs,
    score_song,
)

SONGS_CSV = str(Path(__file__).resolve().parent.parent / "data" / "songs.csv")

POP_PREFS = {"favorite_genre": "pop", "favorite_mood": "happy", "target_energy": 0.8, "likes_acoustic": False}
LOFI_PREFS = {"favorite_genre": "lofi", "favorite_mood": "chill", "target_energy": 0.35, "likes_acoustic": True}

def make_small_recommender() -> Recommender:
    songs = [
        Song(
            id=1,
            title="Test Pop Track",
            artist="Test Artist",
            genre="pop",
            mood="happy",
            energy=0.8,
            tempo_bpm=120,
            valence=0.9,
            danceability=0.8,
            acousticness=0.2,
        ),
        Song(
            id=2,
            title="Chill Lofi Loop",
            artist="Test Artist",
            genre="lofi",
            mood="chill",
            energy=0.4,
            tempo_bpm=80,
            valence=0.6,
            danceability=0.5,
            acousticness=0.9,
        ),
    ]
    return Recommender(songs)


def test_recommend_returns_songs_sorted_by_score():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    results = rec.recommend(user, k=2)

    assert len(results) == 2
    # Starter expectation: the pop, happy, high energy song should score higher
    assert results[0].genre == "pop"
    assert results[0].mood == "happy"


def test_explain_recommendation_returns_non_empty_string():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    song = rec.songs[0]

    explanation = rec.explain_recommendation(user, song)
    assert isinstance(explanation, str)
    assert explanation.strip() != ""


# --- Tests added in Phase 3 -------------------------------------------------

def make_song(**overrides) -> dict:
    """A neutral song dictionary; each test overrides only the fields it checks."""
    song = {
        "id": 1, "title": "Test Song", "artist": "Test Artist", "genre": "rock", "mood": "moody",
        "energy": 0.5, "tempo_bpm": 100.0, "valence": 0.5, "danceability": 0.5, "acousticness": 0.5,
    }
    song.update(overrides)
    return song


def test_load_songs_converts_numeric_fields():
    songs = load_songs(SONGS_CSV)

    assert len(songs) == 18
    assert [song["id"] for song in songs] == list(range(1, 19))
    assert all(isinstance(song["id"], int) for song in songs)
    for field in ("energy", "tempo_bpm", "valence", "danceability", "acousticness"):
        assert all(isinstance(song[field], float) for song in songs)
    assert songs[0]["title"] == "Sunrise City"
    assert songs[0]["energy"] == 0.82
    assert songs[0]["tempo_bpm"] == 118.0


def test_load_songs_reports_bad_rows_clearly(tmp_path):
    header = "id,title,artist,genre,mood,energy,tempo_bpm,valence,danceability,acousticness\n"
    bad_number = tmp_path / "bad_number.csv"
    bad_number.write_text(header + "1,T,A,pop,happy,high,120,0.5,0.5,0.5\n", encoding="utf-8")
    missing_column = tmp_path / "missing_column.csv"
    missing_column.write_text(header.replace(",acousticness", "") + "1,T,A,pop,happy,0.5,120,0.5,0.5\n",
                              encoding="utf-8")

    with pytest.raises(ValueError, match="line 2: energy must be a number"):
        load_songs(str(bad_number))
    with pytest.raises(ValueError, match="missing column"):
        load_songs(str(missing_column))


def test_score_song_explains_each_component():
    score, reasons = score_song(POP_PREFS, make_song(genre="pop", mood="happy", energy=0.82, acousticness=0.18))

    assert score == pytest.approx(3 + 2 + 1.96 + 0.82)
    assert reasons == [
        "genre match: pop (+3.00)",
        "mood match: happy (+2.00)",
        "energy 0.82 is 0.02 from target 0.80 (+1.96)",
        "acousticness 0.18, prefers less acoustic (+0.82)",
    ]


def test_energy_rewards_closeness_not_higher_energy():
    at_target, _ = score_song(LOFI_PREFS, make_song(energy=0.35))
    much_higher, _ = score_song(LOFI_PREFS, make_song(energy=0.95))
    below, _ = score_song(LOFI_PREFS, make_song(energy=0.25))
    above, _ = score_song(LOFI_PREFS, make_song(energy=0.45))

    assert at_target > much_higher
    assert at_target - much_higher == pytest.approx(2 * 0.60)
    assert below == pytest.approx(above)  # same distance in either direction


def test_acoustic_preference_both_directions():
    song = make_song(acousticness=0.9)
    likes_score, likes_reasons = score_song(dict(POP_PREFS, likes_acoustic=True), song)
    prefers_less_score, prefers_less_reasons = score_song(dict(POP_PREFS, likes_acoustic=False), song)

    assert likes_score - prefers_less_score == pytest.approx(0.9 - 0.1)
    assert likes_reasons[3] == "acousticness 0.90, likes acoustic (+0.90)"
    assert prefers_less_reasons[3] == "acousticness 0.90, prefers less acoustic (+0.10)"


def test_genre_and_mood_ignore_spaces_and_capitalization_only():
    messy_prefs = dict(POP_PREFS, favorite_genre="  POP ", favorite_mood="Happy")
    _, reasons = score_song(messy_prefs, make_song(genre="Pop", mood=" happy  "))
    assert reasons[:2] == ["genre match: pop (+3.00)", "mood match: happy (+2.00)"]

    # Related but different labels still don't match (exact matching only).
    _, reasons = score_song(POP_PREFS, make_song(genre="indie pop", mood="cheerful"))
    assert reasons[:2] == ["genre indie pop does not match pop (+0.00)",
                           "mood cheerful does not match happy (+0.00)"]


@pytest.mark.parametrize("prefs, song, error, message", [
    (dict(POP_PREFS, target_energy=1.5), make_song(), ValueError, "target_energy must be from 0 to 1"),
    (dict(POP_PREFS, target_energy="high"), make_song(), TypeError, "target_energy must be a number"),
    (dict(POP_PREFS, likes_acoustic="yes"), make_song(), TypeError, "likes_acoustic must be True or False"),
    (POP_PREFS, make_song(energy=-0.1), ValueError, "song energy must be from 0 to 1"),
    ({"genre": "pop", "mood": "happy", "energy": 0.8}, make_song(), ValueError, "missing required key"),
])
def test_score_song_rejects_invalid_values(prefs, song, error, message):
    with pytest.raises(error, match=message):
        score_song(prefs, song)


def test_recommend_songs_ranks_unsorted_input_without_reordering_it():
    songs = [
        make_song(id=1, title="Worst", energy=0.0, acousticness=1.0),
        make_song(id=2, title="Middle", genre="pop", energy=0.5),
        make_song(id=3, title="Best", genre="pop", mood="happy", energy=0.8, acousticness=0.0),
    ]
    results = recommend_songs(POP_PREFS, songs, k=3)

    assert [song["title"] for song, _, _ in results] == ["Best", "Middle", "Worst"]
    assert [song["id"] for song in songs] == [1, 2, 3]  # caller's list is unchanged
    scores = [score for _, score, _ in results]
    assert scores == sorted(scores, reverse=True)
    assert all(isinstance(reasons, list) and len(reasons) == 4 for _, _, reasons in results)


def test_rounded_ties_keep_input_order():
    night_drive = make_song(title="Night Drive Loop", genre="synthwave", mood="moody",
                            energy=0.75, acousticness=0.22)
    storm_runner = make_song(title="Storm Runner", genre="rock", mood="intense",
                             energy=0.91, acousticness=0.10)
    raw_night, _ = score_song(POP_PREFS, night_drive)
    raw_storm, _ = score_song(POP_PREFS, storm_runner)

    # The raw floats differ by rounding noise, so without rounding Storm Runner would win.
    assert raw_night != raw_storm
    assert round(raw_night, 4) == round(raw_storm, 4) == 2.68

    results = recommend_songs(POP_PREFS, [night_drive, storm_runner], k=2)
    assert [song["title"] for song, _, _ in results] == ["Night Drive Loop", "Storm Runner"]


def test_k_boundaries():
    songs = load_songs(SONGS_CSV)

    assert recommend_songs(POP_PREFS, [], k=5) == []
    assert recommend_songs(POP_PREFS, songs, k=0) == []
    assert len(recommend_songs(POP_PREFS, songs, k=100)) == len(songs)
    with pytest.raises(ValueError, match="k must be 0 or more"):
        recommend_songs(POP_PREFS, songs, k=-1)


def test_lofi_profile_reproduces_expected_top_five():
    results = recommend_songs(LOFI_PREFS, load_songs(SONGS_CSV), k=5)

    assert [(song["title"], score) for song, score, _ in results] == [
        ("Library Rain", 7.86),
        ("Midnight Coding", 7.57),
        ("Focus Flow", 5.68),
        ("Spacewalk Thoughts", 4.78),
        ("Coffee Shop Stories", 2.85),
    ]


def test_class_and_function_interfaces_agree():
    song_dicts = load_songs(SONGS_CSV)
    songs = [Song(**song) for song in song_dicts]

    for prefs in (POP_PREFS, LOFI_PREFS):
        class_titles = [song.title for song in Recommender(songs).recommend(UserProfile(**prefs), k=18)]
        function_titles = [song["title"] for song, _, _ in recommend_songs(prefs, song_dicts, k=18)]
        assert class_titles == function_titles

    _, reasons = score_song(LOFI_PREFS, song_dicts[0])
    explanation = Recommender(songs).explain_recommendation(UserProfile(**LOFI_PREFS), songs[0])
    assert all(reason in explanation for reason in reasons)


def test_recommender_class_ranks_unsorted_input():
    user = UserProfile(favorite_genre="pop", favorite_mood="happy", target_energy=0.8, likes_acoustic=False)
    reversed_songs = list(reversed(make_small_recommender().songs))  # lofi song first

    results = Recommender(reversed_songs).recommend(user, k=2)
    assert [song.title for song in results] == ["Test Pop Track", "Chill Lofi Loop"]


def test_cli_prints_count_profiles_and_recommendations(capsys):
    main()
    output = capsys.readouterr().out

    assert "Loaded 18 songs from data/songs.csv" in output
    assert "Scoring weights: genre 3, mood 2, energy 2, acoustic 1 (max score 8)" in output
    assert "=== High-Energy Pop (default) ===" in output
    assert "  likes_acoustic: False" in output
    assert "1. Sunrise City by Neon Echo  (score 7.78 / 8)" in output
    assert "=== Chill Lofi (verification example) ===" in output
    assert "1. Library Rain by Paper Lanterns  (score 7.86 / 8)" in output
    assert "=== Personal interest: indie pop (provisional) ===" in output
    assert output.count("Top 5 recommendations:") == 6  # all six evaluation profiles
