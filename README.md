# 🎵 Music Recommender Simulation

## Project Summary

In this project you will build and explain a small music recommender system.

Your goal is to:

- Represent songs and a user "taste profile" as data
- Design a scoring rule that turns that data into recommendations
- Evaluate what your system gets right and wrong
- Reflect on how this mirrors real world AI recommenders

Replace this paragraph with your own summary of what your version does.

---

## How The System Works

> **Status: implemented (Phase 3).** The design below is implemented in `src/recommender.py` as `load_songs`, `score_song` and `recommend_songs`. The `Recommender` class reuses the same scoring and ranking code. Run it with `py -m src.main` (or `python -m src.main`); actual output is in [Sample Recommendation Output](#sample-recommendation-output).

### How real recommenders work

Music and video apps usually mix two approaches:

- **Collaborative filtering** uses patterns in *other people's behavior*. If listeners with tastes like yours enjoyed a song, it may be recommended to you, even if the system knows nothing about the song itself ([Google ML course: collaborative filtering](https://developers.google.com/machine-learning/recommendation/collaborative/basics)).
- **Content-based filtering** uses *attributes of the items*, such as genre or mood, and matches them to what a user likes ([Google ML course: content-based filtering](https://developers.google.com/machine-learning/recommendation/content-based/basics)).

These systems learn from signals such as:

- **Listening history, skips and saves.** Spotify says searching, listening, skipping and saving to Your Library shape what it calls your "taste profile". It also considers content characteristics such as genre, and the tastes of users in general ([Spotify: Understanding recommendations](https://www.spotify.com/us/safetyandprivacy/understanding-recommendations)).
- **Likes and dislikes.** YouTube lists clicks, watch time, survey responses, sharing, likes and dislikes as signals, and compares your viewing habits with those of similar viewers ([YouTube: On YouTube's recommendation system](https://blog.youtube/inside-youtube/on-youtubes-recommendation-system/)).
- **Playlists.** Spotify released one million user-created playlists for a 2018 research challenge on recommending tracks to continue a playlist ([Zamani et al.](https://arxiv.org/abs/1810.01520)).

Some signals are *explicit*: the user says directly what they like, such as giving a rating. Others are *implicit*: the system infers interest from behavior, such as what someone plays ([Google ML course](https://developers.google.com/machine-learning/recommendation/collaborative/basics)).

### Our approach

This simulator has no other users and no listening history, so it cannot do collaborative filtering. Instead it uses **content-based filtering with explicit preferences**. The user states their tastes up front in a `UserProfile`, and each song's attributes from `data/songs.csv` are compared against them.

### Dataset

`data/songs.csv` has **18 songs**: the original 10 starter songs (ids 1–10) plus 8 fictional songs added for this project (ids 11–18).

- The added songs bring in genres and moods the starter data lacked (folk, flamenco, metal, r&b, classical, hip hop, reggae and blues). They also add energy and acousticness combinations that were missing, such as high-energy acoustic flamenco and calm electronic r&b.
- **The added titles, artists and feature values are synthetic classroom data.** They were chosen by hand to be plausible, not measured from real audio.
- Every field is filled in. `energy`, `valence`, `danceability` and `acousticness` are between 0 and 1, and `tempo_bpm` is between 60 and 176.

### What each `Song` stores

A `Song` keeps all ten columns of `data/songs.csv`. Only four are used for scoring:

| Field | Meaning | Used in score? |
|---|---|---|
| `id`, `title`, `artist` | Identify the song | No |
| `genre` | Style label, e.g. `pop`, `lofi` | Yes |
| `mood` | Feeling label, e.g. `happy`, `chill` | Yes |
| `energy` | 0–1, how intense or active the song feels | Yes |
| `acousticness` | 0–1, how acoustic (vs. electronic) it sounds | Yes |
| `tempo_bpm` | Speed in beats per minute | No (kept for later) |
| `valence` | 0–1, how positive it sounds | No (kept for later) |
| `danceability` | 0–1, how easy it is to dance to | No (kept for later) |

### What each `UserProfile` stores

| Field | Meaning |
|---|---|
| `favorite_genre` | The genre the user wants |
| `favorite_mood` | The mood the user wants |
| `target_energy` | The energy level (0–1) the user wants |
| `likes_acoustic` | `True` = prefers acoustic songs. `False` = prefers *less* acoustic songs. In this design `False` is a preference, not "no preference". |

### Illustrative user profile

This example profile is used to explain and test the design. It is an illustration, not anyone's personal taste:

```python
user_prefs = {
    "favorite_genre": "lofi",
    "favorite_mood": "chill",
    "target_energy": 0.35,
    "likes_acoustic": True,
}
```

The keys are exactly the `UserProfile` field names above, so the same data can become `UserProfile(**user_prefs)`.

### Scoring: the starting recipe

| Rule | Points |
|---|---|
| Genre matches `favorite_genre` | 3 |
| Mood matches `favorite_mood` | 2 |
| Energy similarity | 2 × (1 − \|song energy − target energy\|), from 0 to 2 |
| Acoustic preference | the song's acousticness if `likes_acoustic` is `True`, otherwise 1 − acousticness, from 0 to 1 |

- **Inputs must be between 0 and 1.** The numeric song features and `target_energy` must be within [0, 1]. With that rule, the **maximum score is 8** (3 + 2 + 2 + 1). Values outside that range, or a `likes_acoustic` that isn't `True` or `False`, stop the program with a clear error.
- **Genre and mood must match exactly** after trimming spaces and ignoring capitalization. `" Pop"` matches `"pop"`, but `"indie pop"` does not.
- **Energy rewards closeness, not "more".** A song exactly at the user's target gets the full 2 points. Songs lose points the further they are from the target in *either* direction, so a user who wants calm music isn't pushed toward the loudest songs.
- **Each score comes with reasons**, one per rule, showing what that rule added. For example: `genre match: pop (+3.00)` or `energy 0.82 is 0.02 from target 0.80 (+1.96)`.

### Ranking: choosing the recommendations

1. Score every song in the catalog.
2. Round each total score to four decimal places and use that as the sorting key.
3. Sort from highest to lowest key. Songs with equal keys keep their original `songs.csv` order.
4. Return the top `k` songs (5 by default).

An empty catalog or `k = 0` returns no songs, a `k` larger than the catalog returns every song, and a negative `k` is an error.

**Why round?** Computers store decimals imprecisely. Two songs that should both score 2.68 can come out as `2.68` and `2.6799999999999997`, and that invisible difference would decide their order. Rounding to four decimal places intentionally treats extremely close scores (ones that agree to four decimal places) as ties, so the CSV order decides instead.

### Data flow

```
User preferences  +  data/songs.csv
                 |
                 v
Calculate each song's score and reasons
                 |
                 v
Sort by rounded score (highest first; ties keep CSV order)
                 |
                 v
Return the top k recommendations
```

### Expected result for the illustrative profile

This top five was calculated outside the program during planning. The implemented program reproduces it exactly, and an automated test checks it:

| Rank | Song | Genre / mood | Score |
|---|---|---|---|
| 1 | Library Rain | lofi / chill | 7.86 |
| 2 | Midnight Coding | lofi / chill | 7.57 |
| 3 | Focus Flow | lofi / focused | 5.68 |
| 4 | Spacewalk Thoughts | ambient / chill | 4.78 |
| 5 | Coffee Shop Stories | jazz / relaxed | 2.85 |

This result applies only to this profile and this catalog. It is not a rule that lofi songs always rank first. The three lofi songs here also happen to be calm and acoustic. A lofi song with a different mood, very different energy and low acousticness could score below 4. A non-lofi song that matches the mood, energy and acoustic preference could score up to 5.

### Known limitations of this design

- **Genre has the largest weight.** A genre match (3 points) is worth as much as perfect energy and acoustic fit combined.
- **Exact labels miss related ones.** "indie pop" doesn't match "pop", and "relaxed" or "peaceful" don't match "chill".
- **There is no neutral acoustic option.** `likes_acoustic=False` means "prefers less acoustic", so a user who doesn't care is still pushed one way.
- **The catalog is small and uneven.** There are 18 songs. Lofi has 3, pop has 2, and every other genre has only 1.
- **This is not evidence of accuracy.** The synthetic values and hand-picked weights are a starting design. They don't show that the recommender would match real people's taste.

---

## Getting Started

### Setup

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows
   ```

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python -m src.main
```

On Windows, if `python` isn't recognized, use the launcher instead: `py -m src.main`.

### Running Tests

Run the tests from the repository root with:

```bash
python -m pytest
```

On Windows you can use `py -m pytest`. Plain `pytest` doesn't add the repository root to Python's import path, so the tests' `from src...` imports fail with it.

You can add more tests in `tests/test_recommender.py`.

---

## Sample Recommendation Output

Actual output of `py -m src.main`, run from the repository root. One run prints two profiles. Both are illustrative examples, not anyone's personal taste.

### Default profile: pop / happy

Profile used: `favorite_genre="pop"`, `favorite_mood="happy"`, `target_energy=0.8`, `likes_acoustic=False`. Here `False` means "prefers less acoustic", chosen to fit the high-energy, mostly electronic pop songs.

```text
Loaded 18 songs from data/songs.csv

=== Default profile: pop / happy ===
Profile:
  favorite_genre: pop
  favorite_mood: happy
  target_energy: 0.8
  likes_acoustic: False

Top 5 recommendations:

1. Sunrise City by Neon Echo  (score 7.78 / 8)
   - genre match: pop (+3.00)
   - mood match: happy (+2.00)
   - energy 0.82 is 0.02 from target 0.80 (+1.96)
   - acousticness 0.18, prefers less acoustic (+0.82)

2. Gym Hero by Max Pulse  (score 5.69 / 8)
   - genre match: pop (+3.00)
   - mood intense does not match happy (+0.00)
   - energy 0.93 is 0.13 from target 0.80 (+1.74)
   - acousticness 0.05, prefers less acoustic (+0.95)

3. Rooftop Lights by Indigo Parade  (score 4.57 / 8)
   - genre indie pop does not match pop (+0.00)
   - mood match: happy (+2.00)
   - energy 0.76 is 0.04 from target 0.80 (+1.92)
   - acousticness 0.35, prefers less acoustic (+0.65)

4. Storm Runner by Voltline  (score 2.68 / 8)
   - genre rock does not match pop (+0.00)
   - mood intense does not match happy (+0.00)
   - energy 0.91 is 0.11 from target 0.80 (+1.78)
   - acousticness 0.10, prefers less acoustic (+0.90)

5. Night Drive Loop by Neon Echo  (score 2.68 / 8)
   - genre synthwave does not match pop (+0.00)
   - mood moody does not match happy (+0.00)
   - energy 0.75 is 0.05 from target 0.80 (+1.90)
   - acousticness 0.22, prefers less acoustic (+0.78)
```

Storm Runner and Night Drive Loop tie at 2.68 after rounding, so they keep their `songs.csv` order. Rooftop Lights gets no genre points because "indie pop" is not an exact match for "pop".

### Separate verification example: lofi / chill

Profile used: `favorite_genre="lofi"`, `favorite_mood="chill"`, `target_energy=0.35`, `likes_acoustic=True`. This is the illustrative profile from [How The System Works](#how-the-system-works), and the program reproduces its expected top five. Same run as above:

```text
=== Verification example: lofi / chill ===
Profile:
  favorite_genre: lofi
  favorite_mood: chill
  target_energy: 0.35
  likes_acoustic: True

Top 5 recommendations:

1. Library Rain by Paper Lanterns  (score 7.86 / 8)
   - genre match: lofi (+3.00)
   - mood match: chill (+2.00)
   - energy 0.35 is 0.00 from target 0.35 (+2.00)
   - acousticness 0.86, likes acoustic (+0.86)

2. Midnight Coding by LoRoom  (score 7.57 / 8)
   - genre match: lofi (+3.00)
   - mood match: chill (+2.00)
   - energy 0.42 is 0.07 from target 0.35 (+1.86)
   - acousticness 0.71, likes acoustic (+0.71)

3. Focus Flow by LoRoom  (score 5.68 / 8)
   - genre match: lofi (+3.00)
   - mood focused does not match chill (+0.00)
   - energy 0.40 is 0.05 from target 0.35 (+1.90)
   - acousticness 0.78, likes acoustic (+0.78)

4. Spacewalk Thoughts by Orbit Bloom  (score 4.78 / 8)
   - genre ambient does not match lofi (+0.00)
   - mood match: chill (+2.00)
   - energy 0.28 is 0.07 from target 0.35 (+1.86)
   - acousticness 0.92, likes acoustic (+0.92)

5. Coffee Shop Stories by Slow Stereo  (score 2.85 / 8)
   - genre jazz does not match lofi (+0.00)
   - mood relaxed does not match chill (+0.00)
   - energy 0.37 is 0.02 from target 0.35 (+1.96)
   - acousticness 0.89, likes acoustic (+0.89)
```

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or demo video link here -->

---

## Experiments You Tried

Use this section to document the experiments you ran. For example:

- What happened when you changed the weight on genre from 2.0 to 0.5
- What happened when you added tempo or valence to the score
- How did your system behave for different types of users

---

## Limitations and Risks

Summarize some limitations of your recommender.

Examples:

- It only works on a tiny catalog
- It does not understand lyrics or language
- It might over favor one genre or mood

You will go deeper on this in your model card.

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

Write 1 to 2 paragraphs here about what you learned:

- about how recommenders turn data into predictions
- about where bias or unfairness could show up in systems like this



