# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name

**VibeFinder 1.0**

---

## 2. Intended Use

**Goal / task:** VibeFinder suggests songs from a small catalog. The user gives a favorite genre, a favorite mood, a target energy level from 0 to 1, and whether they like acoustic music. VibeFinder scores every song and returns the top five. Each suggestion comes with the reasons for its score.

**Intended use:** classroom exploration. VibeFinder is an educational, explainable simulation. It shows how a simple content-based recommender turns stated preferences into a ranked list. It also shows how changing the weights changes that list.

**Assumptions about the user:** The user has one favorite genre and one favorite mood, spelled like the catalog's labels. They have one energy target. Their acoustic preference is yes or no.

**Not intended for:**

- Predicting real people's listening preferences. VibeFinder has not been validated against real listeners.
- Use as a production recommendation service.
- Making decisions about real listeners or artists.

---

## 3. How the Model Works

VibeFinder gives each song a score out of 8. The score adds up four parts:

- **Genre (3 points):** full points if the song's genre matches the user's favorite genre, otherwise 0.
- **Mood (2 points):** full points if the song's mood matches the user's favorite mood, otherwise 0.
- **Energy (up to 2 points):** full points when the song's energy equals the user's target. Points drop the further away the song is, in either direction. So a fan of calm music is not pushed toward loud songs.
- **Acoustic preference (up to 1 point):** if the user likes acoustic music, more acoustic songs earn more. If not, less acoustic songs earn more. There is no "no preference" option.

Genre and mood must match exactly. Extra spaces and capital letters are ignored, but different spellings are not.

Every score comes with reasons. Each reason shows how many points one rule added, for example "genre match: pop (+3.00)".

To recommend songs, VibeFinder scores every song, sorts them from highest to lowest score, and returns the top five (or another number, k). Scores are rounded to four decimal places before sorting, so tiny computer rounding errors cannot break a tie. Tied songs keep their order from the song file.

**Changes from the starter logic:** The starter's loading, scoring and ranking functions were placeholders. They are now implemented. The starter's class-based interface reuses the same scoring code. The command-line app runs six example profiles.

**Baseline and experimental weights:** The weights above (genre 3, mood 2, energy 2, acoustic 1) are the baseline, and they are the current implementation. A Phase 4 experiment used genre 1.5 and energy 4 (maximum 8.5) temporarily. Those experimental weights were then removed. See [section 7](#7-evaluation).

---

## 4. Data

The catalog is `data/songs.csv`. It has **18 songs**.

- **Songs 1–10** came with the starter project. Their source is not documented in this project.
- **Songs 11–18** were added for this project. Their titles, artists and feature values were invented and chosen by hand.

**Features:** Each song has an id, title, artist, genre, mood, energy, tempo (beats per minute), valence, danceability and acousticness. Energy, valence, danceability and acousticness are between 0 and 1.

**Used for scoring:** genre, mood, energy and acousticness. Tempo, valence and danceability are stored but not used.

**Coverage is uneven:**

- There are 15 genres. Lofi has 3 songs and pop has 2. The other 13 genres have 1 song each.
- There are 14 moods. Chill has 3 songs, and happy and intense have 2 each. The other 11 moods have 1 song each.
- There is no Chinese indie or shoegaze. Those are the author's current interests.

**Synthetic-data limits:** The added songs' values were not measured from real audio. The catalog has no listening history, lyrics or language data. So it can show how the formula behaves. It cannot show how well VibeFinder would work for real listeners.

---

## 5. Strengths

These strengths come from the Phase 4 tests in [section 7](#7-evaluation).

- **Clear matches work well.** When a profile's labels exist in the catalog and its preferences agree, the #1 song matches every preference. High-Energy Pop, Chill Lofi and Deep Intense Rock got Sunrise City (7.78), Library Rain (7.86) and Storm Runner (7.88).
- **Energy closeness works as designed.** Library Rain sits exactly at the Chill Lofi target of 0.35 and gets the full 2 energy points. Louder songs score lower for that profile.
- **Every score is explained.** Each suggestion lists the points from each rule. That is how every surprise in section 7 was traced to a cause.
- **Results are reproducible.** The same inputs always give the same ranking, and ties follow a fixed rule.
- **One intuition check matched.** For the personal-interest profile, the baseline's #1 (Rooftop Lights) matched the author's description-based preference. This is one example, not proof of accuracy.

---

## 6. Limitations and Bias

These come from the Phase 4 tests in [section 7](#7-evaluation).

- **Genre dominates.** Genre has the largest weight: 3 of 8 points. With mood, the labels are worth 5 points, more than energy and acousticness combined (3). So the calm, sad blues song (energy 0.30) won a request for energy 0.9 by 3.33 points.
- **Exact labels miss related ones.** "Hip-Hop" did not match the catalog's "hip hop". That cost the only hip hop song its 3 genre points. "indie pop" earns nothing for "pop", and metal earns nothing for "rock".
- **Coverage is uneven.** Lofi has 3 songs. Rock, blues, metal, hip hop and indie pop have 1 each. There is no Chinese indie or shoegaze, so the author's current interests could only be approximated with "indie pop".
- **The acoustic setting has no neutral option.** `likes_acoustic=False` means "prefers less acoustic". Five of the six test profiles used it, so all five were steered toward less acoustic songs.
- **The data is limited.** The catalog is small, the 8 added songs are synthetic, and there is no real listening data. No demographic information was used, and no demographic bias was tested or shown. These tests show how the formula behaves, not how accurate or fair it would be for real listeners.

---

## 7. Evaluation

**Summary:**

- **Six profiles:** High-Energy Pop, Chill Lofi, Deep Intense Rock, two adversarial profiles, and one personal-interest profile.
- **Baseline weights (the implementation):** genre 3, mood 2, energy 2, acoustic 1; maximum 8.
- **Experimental weights (temporary):** genre 1.5, mood 2, energy 4, acoustic 1; maximum 8.5. They were removed after the experiment.
- **Reproducible:** `py -m src.main` prints the same baseline output every time. The experiment was run twice for the first five profiles, with identical output.
- **Tests:** 20 automated tests pass (`py -m pytest`). They check that the code follows the recipe. Passing tests is not proof that the recommendations are accurate.

The details and evidence follow.

### Method

- Ran the real command-line app, `py -m src.main`, on the 18-song catalog in `data/songs.csv`. It prints the scoring weights, then the top five songs, scores and reasons for each of six profiles.
- The baseline recipe is described in [section 3](#3-how-the-model-works).
- Each result was explained from its printed score components. The added songs are invented, with hand-chosen values, so this checks how the formula behaves, not whether the songs sound good or whether real listeners would agree.

### Profiles tested

| Profile | `favorite_genre` | `favorite_mood` | `target_energy` | `likes_acoustic` | What it probes |
|---|---|---|---|---|---|
| High-Energy Pop (default) | pop | happy | 0.8 | False | A common case; two songs are labeled "pop" |
| Chill Lofi (verification example) | lofi | chill | 0.35 | True | The best-covered genre, with three lofi songs |
| Deep Intense Rock | rock | intense | 0.9 | False | A genre with only one song in the catalog |
| Adversarial: sad mood + high energy | blues | sad | 0.9 | False | Conflicting preferences: the labels point to the only sad song, which is calm (energy 0.30), while the energy target asks for loud music |
| Adversarial: "Hip-Hop" spelling | Hip-Hop | confident | 0.7 | False | Exact labels: the catalog says "hip hop"; normalization fixes capitalization but not the hyphen |
| Personal interest: indie pop (provisional) | indie pop | moody | 0.7 | False | The author's interests, approximated with the closest label the catalog has; only one song (Rooftop Lights) is labeled "indie pop" |

The first five are illustrative test profiles, not anyone's personal taste. The sixth is based on the author's confirmed interest in Chinese indie and Korean shoegaze. Neither genre is in the catalog, so it uses "indie pop", the closest available label. Its mood, energy and acoustic values are provisional test assumptions, not confirmed preferences.

### Baseline results

The top five for every profile appear in the comparison tables under [Experiment: weight shift](#experiment-weight-shift). Full baseline terminal output for High-Energy Pop and Chill Lofi is in the README's [Sample Recommendation Output](README.md#sample-recommendation-output); the other four profiles are shown below.

**Why each #1 song won:**

- **High-Energy Pop: Sunrise City, 7.78.** Genre 3 + mood 2 + energy 1.96 (0.82 vs. target 0.80) + acoustic 0.82. It is the only song labeled both "pop" and "happy".
- **Chill Lofi: Library Rain, 7.86.** Genre 3 + mood 2 + energy 2.00 (exactly 0.35) + acoustic 0.86.
- **Deep Intense Rock: Storm Runner, 7.88.** Genre 3 + mood 2 + energy 1.98 (0.91 vs. 0.90) + acoustic 0.90. It is the catalog's only rock song.
- **Sad mood + high energy: Rain on Route 9, 6.22.** Genre 3 + mood 2 + energy only 0.80 (0.30 is 0.60 below the target) + acoustic 0.42. It won by 3.33 points despite the worst energy fit in the top five, because its two label matches (5 points) outweigh the most any other song can earn from energy and acousticness (3 points).
- **"Hip-Hop" spelling: Corner Store Kings, 4.82.** Genre 0 ("hip hop" does not match "hip-hop") + mood 2 + energy 1.92 + acoustic 0.90. It won on mood and energy alone; with the catalog's spelling, the same profile would give it 7.82.
- **Personal interest (indie pop): Rooftop Lights, 5.53.** Genre 3 (the catalog's only "indie pop" song) + mood 0 (it is labeled "happy", not "moody") + energy 1.88 (0.76 vs. 0.70) + acoustic 0.65. It beat Night Drive Loop (synthwave, moody, 4.68) by 0.85 points because its genre match (3) is worth more than Night Drive's mood match (2). Their energy fits are nearly equal (0.06 vs. 0.05 from the target), and Night Drive's lower acousticness (0.22 vs. 0.35) narrows the gap. Ranking #1 only means this song fits the profile's labels and numbers best under this formula. It is not evidence that the starter song sounds like the music the author enjoys, and the author has not listened to it.

**Surprises:**

- For High-Energy Pop, Gym Hero (pop, but "intense") ranks #2, above Rooftop Lights ("indie pop", "happy", closer energy). The exact genre match is worth 3 points and the mood match only 2, and "indie pop" earns nothing for "pop".
- For Deep Intense Rock, the #2 song is pop (Gym Hero, which shares the "intense" mood), and the metal song ranks #3 on energy and acousticness alone. With one rock song in the catalog, everything after #1 comes from other genres.
- For sad mood + high energy, the winner is the calmest song in the top five. Ranks #2 to #4 are within 0.05 points of each other (2.89, 2.88, 2.84), so small energy and acousticness differences decide their order.
- For "Hip-Hop", one hyphen cost the only hip hop song its 3 genre points.
- For the personal-interest profile, the two "pop" songs (Sunrise City and Gym Hero) earn no genre points for "indie pop", the mirror image of Rooftop Lights earning none for "pop". The author's actual genres, Chinese indie and Korean shoegaze, cannot be requested at all.
- High-Energy Pop has a tie at 2.68 after rounding (Storm Runner and Night Drive Loop), which the tie rule resolves by CSV order.

These are observations about the scoring formula. Whether Gym Hero is a better pop pick than Rooftop Lights, or whether a listener asking for sad music would want a loud song, is a question of musical taste that this evaluation does not measure.

### Personal intuition check

For the personal-interest profile, the author's feedback was:

> "Based on the descriptions, I would prefer Rooftop Lights because it is indie pop, which is closer to the music I am interested in right now."

In this example, the baseline ranking matches the author's stated preference better: the baseline puts Rooftop Lights first, while the weight experiment puts Night Drive Loop first. The judgment is based on the songs' genre descriptions; the author did not listen to them. It is one judgment about one profile, so it does not show that the baseline is more accurate overall. The High-Energy Pop comparison remains an objective experiment result; no personal preference was recorded for that profile.

#### Baseline output: Deep Intense Rock

```text
=== Deep Intense Rock ===
Profile:
  favorite_genre: rock
  favorite_mood: intense
  target_energy: 0.9
  likes_acoustic: False

Top 5 recommendations:

1. Storm Runner by Voltline  (score 7.88 / 8)
   - genre match: rock (+3.00)
   - mood match: intense (+2.00)
   - energy 0.91 is 0.01 from target 0.90 (+1.98)
   - acousticness 0.10, prefers less acoustic (+0.90)

2. Gym Hero by Max Pulse  (score 4.89 / 8)
   - genre pop does not match rock (+0.00)
   - mood match: intense (+2.00)
   - energy 0.93 is 0.03 from target 0.90 (+1.94)
   - acousticness 0.05, prefers less acoustic (+0.95)

3. Iron Verdict by Grave Signal  (score 2.84 / 8)
   - genre metal does not match rock (+0.00)
   - mood angry does not match intense (+0.00)
   - energy 0.97 is 0.07 from target 0.90 (+1.86)
   - acousticness 0.02, prefers less acoustic (+0.98)

4. Sunrise City by Neon Echo  (score 2.66 / 8)
   - genre pop does not match rock (+0.00)
   - mood happy does not match intense (+0.00)
   - energy 0.82 is 0.08 from target 0.90 (+1.84)
   - acousticness 0.18, prefers less acoustic (+0.82)

5. Night Drive Loop by Neon Echo  (score 2.48 / 8)
   - genre synthwave does not match rock (+0.00)
   - mood moody does not match intense (+0.00)
   - energy 0.75 is 0.15 from target 0.90 (+1.70)
   - acousticness 0.22, prefers less acoustic (+0.78)
```

#### Baseline output: sad mood + high energy

```text
=== Adversarial: sad mood + high energy ===
Profile:
  favorite_genre: blues
  favorite_mood: sad
  target_energy: 0.9
  likes_acoustic: False

Top 5 recommendations:

1. Rain on Route 9 by Delta Smoke  (score 6.22 / 8)
   - genre match: blues (+3.00)
   - mood match: sad (+2.00)
   - energy 0.30 is 0.60 from target 0.90 (+0.80)
   - acousticness 0.58, prefers less acoustic (+0.42)

2. Gym Hero by Max Pulse  (score 2.89 / 8)
   - genre pop does not match blues (+0.00)
   - mood intense does not match sad (+0.00)
   - energy 0.93 is 0.03 from target 0.90 (+1.94)
   - acousticness 0.05, prefers less acoustic (+0.95)

3. Storm Runner by Voltline  (score 2.88 / 8)
   - genre rock does not match blues (+0.00)
   - mood intense does not match sad (+0.00)
   - energy 0.91 is 0.01 from target 0.90 (+1.98)
   - acousticness 0.10, prefers less acoustic (+0.90)

4. Iron Verdict by Grave Signal  (score 2.84 / 8)
   - genre metal does not match blues (+0.00)
   - mood angry does not match sad (+0.00)
   - energy 0.97 is 0.07 from target 0.90 (+1.86)
   - acousticness 0.02, prefers less acoustic (+0.98)

5. Sunrise City by Neon Echo  (score 2.66 / 8)
   - genre pop does not match blues (+0.00)
   - mood happy does not match sad (+0.00)
   - energy 0.82 is 0.08 from target 0.90 (+1.84)
   - acousticness 0.18, prefers less acoustic (+0.82)
```

#### Baseline output: "Hip-Hop" spelling

```text
=== Adversarial: 'Hip-Hop' spelling ===
Profile:
  favorite_genre: Hip-Hop
  favorite_mood: confident
  target_energy: 0.7
  likes_acoustic: False

Top 5 recommendations:

1. Corner Store Kings by Block Theory  (score 4.82 / 8)
   - genre hip hop does not match hip-hop (+0.00)
   - mood match: confident (+2.00)
   - energy 0.66 is 0.04 from target 0.70 (+1.92)
   - acousticness 0.10, prefers less acoustic (+0.90)

2. Night Drive Loop by Neon Echo  (score 2.68 / 8)
   - genre synthwave does not match hip-hop (+0.00)
   - mood moody does not match confident (+0.00)
   - energy 0.75 is 0.05 from target 0.70 (+1.90)
   - acousticness 0.22, prefers less acoustic (+0.78)

3. Sunrise City by Neon Echo  (score 2.58 / 8)
   - genre pop does not match hip-hop (+0.00)
   - mood happy does not match confident (+0.00)
   - energy 0.82 is 0.12 from target 0.70 (+1.76)
   - acousticness 0.18, prefers less acoustic (+0.82)

4. Rooftop Lights by Indigo Parade  (score 2.53 / 8)
   - genre indie pop does not match hip-hop (+0.00)
   - mood happy does not match confident (+0.00)
   - energy 0.76 is 0.06 from target 0.70 (+1.88)
   - acousticness 0.35, prefers less acoustic (+0.65)

5. Gym Hero by Max Pulse  (score 2.49 / 8)
   - genre pop does not match hip-hop (+0.00)
   - mood intense does not match confident (+0.00)
   - energy 0.93 is 0.23 from target 0.70 (+1.54)
   - acousticness 0.05, prefers less acoustic (+0.95)
```

#### Baseline output: personal interest (indie pop)

```text
=== Personal interest: indie pop (provisional) ===
Profile:
  favorite_genre: indie pop
  favorite_mood: moody
  target_energy: 0.7
  likes_acoustic: False

Top 5 recommendations:

1. Rooftop Lights by Indigo Parade  (score 5.53 / 8)
   - genre match: indie pop (+3.00)
   - mood happy does not match moody (+0.00)
   - energy 0.76 is 0.06 from target 0.70 (+1.88)
   - acousticness 0.35, prefers less acoustic (+0.65)

2. Night Drive Loop by Neon Echo  (score 4.68 / 8)
   - genre synthwave does not match indie pop (+0.00)
   - mood match: moody (+2.00)
   - energy 0.75 is 0.05 from target 0.70 (+1.90)
   - acousticness 0.22, prefers less acoustic (+0.78)

3. Corner Store Kings by Block Theory  (score 2.82 / 8)
   - genre hip hop does not match indie pop (+0.00)
   - mood confident does not match moody (+0.00)
   - energy 0.66 is 0.04 from target 0.70 (+1.92)
   - acousticness 0.10, prefers less acoustic (+0.90)

4. Sunrise City by Neon Echo  (score 2.58 / 8)
   - genre pop does not match indie pop (+0.00)
   - mood happy does not match moody (+0.00)
   - energy 0.82 is 0.12 from target 0.70 (+1.76)
   - acousticness 0.18, prefers less acoustic (+0.82)

5. Gym Hero by Max Pulse  (score 2.49 / 8)
   - genre pop does not match indie pop (+0.00)
   - mood intense does not match moody (+0.00)
   - energy 0.93 is 0.23 from target 0.70 (+1.54)
   - acousticness 0.05, prefers less acoustic (+0.95)
```

### Experiment: weight shift

**Change:** genre 3 → 1.5 (halved) and energy 2 → 4 (doubled, so energy similarity is 4 × (1 − gap)). Mood stays 2 and acoustic stays 1. The maximum score becomes 8.5.

**Method:** The constants `GENRE_POINTS` and `ENERGY_POINTS` in `src/recommender.py` were changed temporarily, the same profiles were run through `py -m src.main`, and then the original values were restored. The personal-interest profile was added after the first experiment run, so the experiment was repeated for all six profiles; the first five produced identical output both times. After each restore, the 20 tests passed and the CLI output was byte-identical to the baseline run. The baseline weights remain the implementation.

**Prediction (made before running):**

- High-Energy Pop: Sunrise City stays #1, Rooftop Lights passes Gym Hero, and Night Drive Loop moves ahead of Storm Runner.
- Chill Lofi: Library Rain stays #1 and Spacewalk Thoughts passes Focus Flow.
- Deep Intense Rock: no change.
- Sad mood + high energy: Rain on Route 9 stays #1, but its lead shrinks sharply; Gym Hero and Storm Runner may swap.
- "Hip-Hop" spelling: Corner Store Kings stays #1; lower ranks reorder by energy closeness, and Gym Hero probably drops out.
- Personal interest (added later, and predicted before its own experiment run): Night Drive Loop passes Rooftop Lights for #1, because Rooftop Lights' lead comes from genre (3) beating mood (2), and halving genre reverses that. Storm Runner replaces Gym Hero at #5.

**Result:** Every prediction held. The #1 song changed for one profile: for the personal-interest profile, Night Drive Loop passed Rooftop Lights.

Experimental terminal output (score lines only; each song's four reason lines are omitted for length):

```text
Scoring weights: genre 1.5, mood 2, energy 4, acoustic 1 (max score 8.5)

=== High-Energy Pop (default) ===
1. Sunrise City by Neon Echo  (score 8.24 / 8.5)
2. Rooftop Lights by Indigo Parade  (score 6.49 / 8.5)
3. Gym Hero by Max Pulse  (score 5.93 / 8.5)
4. Night Drive Loop by Neon Echo  (score 4.58 / 8.5)
5. Storm Runner by Voltline  (score 4.46 / 8.5)

=== Chill Lofi (verification example) ===
1. Library Rain by Paper Lanterns  (score 8.36 / 8.5)
2. Midnight Coding by LoRoom  (score 7.93 / 8.5)
3. Spacewalk Thoughts by Orbit Bloom  (score 6.64 / 8.5)
4. Focus Flow by LoRoom  (score 6.08 / 8.5)
5. Coffee Shop Stories by Slow Stereo  (score 4.81 / 8.5)

=== Deep Intense Rock ===
1. Storm Runner by Voltline  (score 8.36 / 8.5)
2. Gym Hero by Max Pulse  (score 6.83 / 8.5)
3. Iron Verdict by Grave Signal  (score 4.70 / 8.5)
4. Sunrise City by Neon Echo  (score 4.50 / 8.5)
5. Night Drive Loop by Neon Echo  (score 4.18 / 8.5)

=== Adversarial: sad mood + high energy ===
1. Rain on Route 9 by Delta Smoke  (score 5.52 / 8.5)
2. Storm Runner by Voltline  (score 4.86 / 8.5)
3. Gym Hero by Max Pulse  (score 4.83 / 8.5)
4. Iron Verdict by Grave Signal  (score 4.70 / 8.5)
5. Sunrise City by Neon Echo  (score 4.50 / 8.5)

=== Adversarial: 'Hip-Hop' spelling ===
1. Corner Store Kings by Block Theory  (score 6.74 / 8.5)
2. Night Drive Loop by Neon Echo  (score 4.58 / 8.5)
3. Rooftop Lights by Indigo Parade  (score 4.41 / 8.5)
4. Sunrise City by Neon Echo  (score 4.34 / 8.5)
5. Storm Runner by Voltline  (score 4.06 / 8.5)

=== Personal interest: indie pop (provisional) ===
1. Night Drive Loop by Neon Echo  (score 6.58 / 8.5)
2. Rooftop Lights by Indigo Parade  (score 5.91 / 8.5)
3. Corner Store Kings by Block Theory  (score 4.74 / 8.5)
4. Sunrise City by Neon Echo  (score 4.34 / 8.5)
5. Storm Runner by Voltline  (score 4.06 / 8.5)
```

#### High-Energy Pop (default)

| Rank | Baseline (max 8) | Experiment (max 8.5) | Change |
|---|---|---|---|
| 1 | Sunrise City 7.78 | Sunrise City 8.24 | same |
| 2 | Gym Hero 5.69 | Rooftop Lights 6.49 | Rooftop Lights was #3 |
| 3 | Rooftop Lights 4.57 | Gym Hero 5.93 | Gym Hero was #2 |
| 4 | Storm Runner 2.68 | Night Drive Loop 4.58 | Night Drive Loop was #5 |
| 5 | Night Drive Loop 2.68 | Storm Runner 4.46 | Storm Runner was #4 |

**What changed and why:** Rooftop Lights rose from #3 to #2 and Gym Hero fell to #3. Gym Hero's genre match is now worth 1.5 instead of 3, while Rooftop Lights' closer energy (0.04 from the target, versus 0.13 for Gym Hero) now counts double. The 2.68 tie also broke: Night Drive Loop (0.05 from the target) moved ahead of Storm Runner (0.11). Sunrise City stayed #1 because it matches every preference.

#### Chill Lofi (verification example)

| Rank | Baseline (max 8) | Experiment (max 8.5) | Change |
|---|---|---|---|
| 1 | Library Rain 7.86 | Library Rain 8.36 | same |
| 2 | Midnight Coding 7.57 | Midnight Coding 7.93 | same |
| 3 | Focus Flow 5.68 | Spacewalk Thoughts 6.64 | Spacewalk Thoughts was #4 |
| 4 | Spacewalk Thoughts 4.78 | Focus Flow 6.08 | Focus Flow was #3 |
| 5 | Coffee Shop Stories 2.85 | Coffee Shop Stories 4.81 | same |

**What changed and why:** Ranks #1, #2 and #5 stayed the same; Library Rain and Midnight Coding match both labels and sit close to 0.35. Spacewalk Thoughts (ambient, chill) passed Focus Flow (lofi, focused) because a mood match (2 points) is now worth more than a genre match (1.5), and their energy gaps are similar (0.07 and 0.05).

#### Deep Intense Rock

| Rank | Baseline (max 8) | Experiment (max 8.5) | Change |
|---|---|---|---|
| 1 | Storm Runner 7.88 | Storm Runner 8.36 | same |
| 2 | Gym Hero 4.89 | Gym Hero 6.83 | same |
| 3 | Iron Verdict 2.84 | Iron Verdict 4.70 | same |
| 4 | Sunrise City 2.66 | Sunrise City 4.50 | same |
| 5 | Night Drive Loop 2.48 | Night Drive Loop 4.18 | same |

**What stayed the same and why:** Nothing changed. Storm Runner matches every preference, and Gym Hero keeps #2 through its mood match and close energy. The other three songs were already in order of energy closeness (0.07, 0.08 and 0.15 from the target), with acousticness pointing the same way, so doubling energy only widened the gaps.

#### Adversarial: sad mood + high energy

| Rank | Baseline (max 8) | Experiment (max 8.5) | Change |
|---|---|---|---|
| 1 | Rain on Route 9 6.22 | Rain on Route 9 5.52 | same |
| 2 | Gym Hero 2.89 | Storm Runner 4.86 | Storm Runner was #3 |
| 3 | Storm Runner 2.88 | Gym Hero 4.83 | Gym Hero was #2 |
| 4 | Iron Verdict 2.84 | Iron Verdict 4.70 | same |
| 5 | Sunrise City 2.66 | Sunrise City 4.50 | same |

**What changed and why:** Rain on Route 9 stayed #1, but its lead over #2 fell from 3.33 to 0.66 points. It lost 1.5 genre points, and its 0.60 energy gap now costs twice as much. Storm Runner (0.01 from the target) passed Gym Hero (0.03 away) because energy closeness now outweighs Gym Hero's small acousticness edge (0.95 vs. 0.90).

#### Adversarial: 'Hip-Hop' spelling

| Rank | Baseline (max 8) | Experiment (max 8.5) | Change |
|---|---|---|---|
| 1 | Corner Store Kings 4.82 | Corner Store Kings 6.74 | same |
| 2 | Night Drive Loop 2.68 | Night Drive Loop 4.58 | same |
| 3 | Sunrise City 2.58 | Rooftop Lights 4.41 | Rooftop Lights was #4 |
| 4 | Rooftop Lights 2.53 | Sunrise City 4.34 | Sunrise City was #3 |
| 5 | Gym Hero 2.49 | Storm Runner 4.06 | Storm Runner new in top five |

Dropped out of the top five: Gym Hero.

**What changed and why:** Halving the genre weight had no effect, because no song matched "hip-hop". Corner Store Kings stayed #1 on mood and energy. Doubling energy reordered the rest by closeness to 0.7: Rooftop Lights (0.06 away) passed Sunrise City (0.12 away), and Storm Runner (0.21 away) replaced Gym Hero (0.23 away) at #5.

#### Personal interest: indie pop (provisional)

| Rank | Baseline (max 8) | Experiment (max 8.5) | Change |
|---|---|---|---|
| 1 | Rooftop Lights 5.53 | Night Drive Loop 6.58 | Night Drive Loop was #2 |
| 2 | Night Drive Loop 4.68 | Rooftop Lights 5.91 | Rooftop Lights was #1 |
| 3 | Corner Store Kings 2.82 | Corner Store Kings 4.74 | same |
| 4 | Sunrise City 2.58 | Sunrise City 4.34 | same |
| 5 | Gym Hero 2.49 | Storm Runner 4.06 | Storm Runner new in top five |

Dropped out of the top five: Gym Hero.

**What changed and why:** This is the only profile whose #1 changed. Rooftop Lights' baseline lead came from its genre match (3) beating Night Drive Loop's mood match (2). With genre halved to 1.5, the mood match is worth more, and the two songs' nearly equal energy fits (0.06 vs. 0.05 from the target) keep the energy points close, so Night Drive Loop wins 6.58 to 5.91. Storm Runner (0.21 away) replaced Gym Hero (0.23 away) at #5. The author's stated preference, based on genre descriptions, matches the baseline order here (see [Personal intuition check](#personal-intuition-check)).

**What the experiment shows:** Halving genre and doubling energy shifts influence from labels toward energy closeness. Most changes were below the #1 spot; the #1 song changed for one of the six profiles. A different ranking is not evidence of better recommendations: apart from the author's one description-based judgment, there are no listener judgments to compare against, and the catalog is small, and the 8 added songs are synthetic. The baseline weights were restored and remain the final implementation.

---

## 8. Future Work

Possible improvements, each linked to a limitation in [section 6](#6-limitations-and-bias):

1. **Genre aliases and related genres.** Treat spellings like "Hip-Hop" and "hip hop" as the same genre. Give partial points to related genres, such as "indie pop" for a "pop" fan. This targets the exact-label misses.
2. **An acoustic target instead of yes/no.** Let users choose an acoustic level from 0 to 1, or "no preference". This targets the missing neutral option.
3. **A broader catalog.** Add more songs per genre, including Chinese indie and Korean shoegaze. This targets the thin, uneven coverage.

---

## 9. Personal Reflection

A short version is below. The full reflection is in the README's [Reflection](README.md#reflection) section.

- **What I learned about recommender systems:** VibeFinder uses content-based filtering. It matches stated preferences to song attributes. Collaborative filtering uses patterns in other users' behavior instead, and real systems can combine both approaches.
- **Something interesting I discovered:** Changing the weights changes what the recommender prioritizes. With genre halved and energy doubled, my personal-interest profile's #1 changed from Rooftop Lights to Night Drive Loop.
- **What this means for music apps:** A few simple rules can produce results that look personalized. That does not mean they match what a listener actually enjoys.
