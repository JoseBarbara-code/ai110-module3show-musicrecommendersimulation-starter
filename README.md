# 🎵 Music Recommender Simulation

## Project Summary

**VibeFinder 1.0** is a small, explainable music recommender built for a CodePath classroom simulation. You give it a favorite genre, a favorite mood, a target energy level from 0 to 1, and whether you like acoustic music. It scores all 18 songs in `data/songs.csv` and prints the top five, with the points each rule added.

It uses content-based filtering: it matches stated preferences to song attributes. It does not learn from other users' behavior. The baseline weights are hand-picked: genre 3, mood 2, energy 2 and acoustic 1, for a maximum of 8.

The project tested six profiles and one weight-shift experiment. See [Experiments You Tried](#experiments-you-tried) and the [model card](model_card.md) for results and limitations.

---

## How The System Works

> **Status: implemented.** The design below is implemented in `src/recommender.py` as `load_songs`, `score_song` and `recommend_songs`. The `Recommender` class reuses the same scoring and ranking code. Run it with `py -m src.main` (or `python -m src.main`); actual output is in [Sample Recommendation Output](#sample-recommendation-output).

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
- **This is not evidence of accuracy.** The hand-picked weights are a starting design, and the 8 added songs are synthetic. They don't show that the recommender would match real people's taste.

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

Excerpts from the actual output of `py -m src.main`, run from the repository root. One run prints the scoring weights and six profiles. The first two are shown here; the other four are in [model_card.md](model_card.md#7-evaluation). These two are illustrative examples, not anyone's personal taste.

### High-Energy Pop (default profile)

Profile used: `favorite_genre="pop"`, `favorite_mood="happy"`, `target_energy=0.8`, `likes_acoustic=False`. Here `False` means "prefers less acoustic", chosen to fit the high-energy, mostly electronic pop songs.

```text
Loaded 18 songs from data/songs.csv
Scoring weights: genre 3, mood 2, energy 2, acoustic 1 (max score 8)

=== High-Energy Pop (default) ===
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

### Chill Lofi (separate verification example)

Profile used: `favorite_genre="lofi"`, `favorite_mood="chill"`, `target_energy=0.35`, `likes_acoustic=True`. This is the illustrative profile from [How The System Works](#how-the-system-works), and the program reproduces its expected top five. Same run as above:

```text
=== Chill Lofi (verification example) ===
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

---

## Experiments You Tried

Full profiles, terminal output and comparisons are in [model_card.md, section 7 (Evaluation)](model_card.md#7-evaluation).

- **Six test profiles.** High-Energy Pop, Chill Lofi and Deep Intense Rock; two adversarial profiles (a sad mood with a high energy target, and "Hip-Hop" spelled differently from the catalog's "hip hop"); and a personal-interest profile. The author enjoys Chinese indie and Korean shoegaze, which the catalog doesn't include, so that profile uses "indie pop", with provisional mood, energy and acoustic values. All were run through `py -m src.main`.
- **What stood out.** Exact labels dominate the baseline. The calm, sad blues song won a request for energy 0.9 by 3.33 points, and the hyphen in "Hip-Hop" cost the only hip hop song its 3 genre points. The rock profile had just one rock song to choose from. For the personal-interest profile, Rooftop Lights (the only indie pop song) ranked #1 on its genre match, even though it is labeled "happy" rather than "moody".
- **Weight shift (genre 3 → 1.5, energy 2 → 4, maximum 8.5).** Applied temporarily in `src/recommender.py`. The #1 song stayed the same for five of the six profiles. For the personal-interest profile, Night Drive Loop (synthwave, moody) passed Rooftop Lights, because a mood match now outweighs a genre match. Lower ranks moved toward songs with closer energy: Rooftop Lights passed Gym Hero for High-Energy Pop, and Spacewalk Thoughts passed Focus Flow for Chill Lofi. Deep Intense Rock did not change at all.
- **Outcome.** The baseline weights were restored and remain the implementation. A different ranking shows what the weights control; it is not evidence of better accuracy.
- **Personal intuition check.** For the personal-interest profile, the author said: "Based on the descriptions, I would prefer Rooftop Lights because it is indie pop, which is closer to the music I am interested in right now." In this example the baseline matches that stated preference better: it ranks Rooftop Lights first, while the experiment puts Night Drive Loop first. The judgment is based on genre descriptions, not on listening to the songs, and one example does not show that the baseline is more accurate overall.

---

## Limitations and Risks

These were observed in testing. Details are in the [model card](model_card.md#6-limitations-and-bias).

- **Small catalog with 8 synthetic songs.** There are 18 songs. The 8 added songs have invented titles and artists and hand-chosen values. Results show how the formula behaves, not real-world accuracy.
- **Uneven coverage.** Lofi has 3 songs and pop has 2; every other genre has 1. There is no Chinese indie or shoegaze.
- **Genre dominates.** Genre and mood labels are worth 5 of 8 points. A calm, sad blues song (energy 0.30) won a sad-blues request with a 0.9 energy target.
- **Exact labels.** "Hip-Hop" does not match "hip hop", and "indie pop" does not match "pop".
- **No neutral acoustic option.** `likes_acoustic=False` means "prefers less acoustic", not "no preference".
- **No lyrics, language or listening history.** VibeFinder cannot learn from what people actually play, like or skip.
- **Risk: results can look more personal than they are.** Each list is tailored to four stated preferences and comes with reasons. But VibeFinder is not validated against real listeners, so it should not be treated as a real recommendation service.

---

## Reflection

The full model card is in [model_card.md](model_card.md).

**Biggest learning moment.** My biggest learning moment was seeing that changing the weights changes what the recommender prioritizes. In the weight-shift experiment, genre was halved and energy was doubled. For my personal-interest profile, Rooftop Lights dropped from #1 to #2, and Night Drive Loop took #1. The songs and my profile did not change. Only the weights did.

**How recommenders turn data into recommendations.** This project uses content-based filtering. It matches my stated preferences to each song's attributes: genre, mood, energy and acousticness. I also learned that collaborative filtering uses patterns in other users' behavior. Real systems can combine both approaches.

**How AI tools helped, and when we double-checked them.** Claude implemented the code and explained each step. Copilot independently checked the files, calculations and tests. For example, it reproduced the expected top-five scores and ran all 20 tests. The tools also needed checking. At one point, Copilot flagged my genre interests as unsupported. It did not have the earlier conversation where I stated them. I clarified that I had stated them explicitly.

**Simple rules, personalized-looking results.** VibeFinder uses four simple rules and fixed weights. Still, each profile gets its own top five with reasons, so the results look personalized. But the system only knows labels and numbers. I currently enjoy Chinese indie and Korean shoegaze, including Parannoul, No Party For Cao Dong, 蛙池 and Omnipotent Youth Society. The catalog has neither genre, so my profile used "indie pop" as the closest label. Its mood, energy and acoustic settings remain provisional assumptions. Based on its indie-pop description, I preferred Rooftop Lights. I did not listen to the song. This also shows where unfairness could appear. Listeners whose genres are missing, or spelled differently, get weaker matches. For example, "Hip-Hop" did not match the catalog's "hip hop".

**What I could try next.** Some possibilities:

- Treat spellings like "Hip-Hop" and "hip hop" as the same, and give partial points to related genres.
- Replace the acoustic yes/no setting with a target level or a "no preference" option.
- Add more songs per genre, including Chinese indie and Korean shoegaze.
- Combine content-based scoring with collaborative signals, such as likes or skips.



