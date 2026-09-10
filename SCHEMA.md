# Schema

Every dataset writes the same tables. Code written against `toy` runs
unchanged against `large`. Column names deliberately mirror the real
pipeline so that Phase 7 (transition to real data) is a join, not a rewrite.

## Where each table comes from in the real project

| synthetic file | real counterpart |
|---|---|
| `teams.csv` | `team_roster/master/teams_master_{gender}_{season}_*.csv` |
| `players.csv` | `team_roster/master/players_master_{gender}_{season}_*.csv` |
| `coaches.csv` | **does not exist** — see MENTOR_NOTES §"Gaps in the real data" |
| `games.csv` | `team_roster/master/results_master_men_*.csv` |
| `submissions.csv` | `data/collegebasketball/reddit/<run>/submissions.csv` |
| `comments.csv` | `data/collegebasketball/reddit/<run>/comments.csv` |
| `comment_entities.csv` | `benchmark_experiments/data/golden_annotations/provisional_dataset_20260620T184018Z_v2.ndjson` — the **adjudicated** gold, 602 comments |
| `comment_entities_annotators.csv` (the annotated sample) | `data/dataset_v2_20k/canonical/annotations_corrected.ndjson` — pre-adjudication, per annotator |
| `comment_labels_weak.csv` | `data/dataset_v2_20k/universe.parquet` |
| `users.csv` | derived from the author columns of `comments.csv` (no real user table exists) |

---

## `comment_entities.csv` — read this one first

**One row per (comment, target entity).** This is the atomic unit of the whole
dataset. It is *not* one row per comment: a single comment can name three
people and abuse only one of them.

| column | type | meaning |
|---|---|---|
| `comment_id` | str | FK → `comments.csv` |
| `entity_id` | str | unique id for this target mention |
| `entity_text` | str | the surface form as written ("Marcus Whitlock", "the refs") |
| `entity_type` | str | `player NCAA` / `team` / `coach` / `player non-NCAA` / `fan(s)` / `referee` / `other` / `unknown` (1.5% of real entities have no type) |
| `target_id` | str | resolved id: a `player_id`, a `team_id`, a `coach_id`, or **empty** |
| `target_team_id` | str | team the target belongs to (empty for refs/fans/other) |
| `is_abusive` | str | **`YES` / `NO`** — this is the *adjudicated* label. `UNSURE` exists only in the per-annotator layer. |
| `diff_profanity`, `diff_meaning_shift`, `diff_reference_complexity`, `diff_common_words` | bool | observable difficulty flags; what the annotated sample sampler stratifies on. No model output involved. |
| `is_severe_abuse`, `insult_derogation`, `threat`, `wish_of_harm`, `sexual_harassment`, `race_hate`, `gender_hate`, `religious_hate`, `profanity_obscene` | str | `YES`/`NO`; only meaningful where `is_abusive == YES` |
| `motive_performance`, `motive_officiating`, `motive_gambling`, `motive_fandom_rivalry`, `motive_appearance`, `motive_personal_life`, `motive_injury`, `motive_coaching` | str | `YES`/`NO` |
| `sarcasm`, `humor`, `implicit_target`, `quotation_reported_speech` | str | `YES`/`NO` |
| `interpretation_needs_history` | str | `NO` / `ROOT_SUBMISSION` / `PARENT` |
| `target_recoverable_from_history` | str | `YES`/`NO` |
| `target_id_unknown` | str | `YES` when `target_id` is empty |

**18% of rows have no `target_id`** — matching the real gold (211 of 1,170).
Not only referees and fans: also players and teams the annotator could not pin
down. They are real interactions with no node to point at. Dropping them,
keeping them as one node per type, and keeping them as one node per comment are
all defensible; doing it silently is not, and the choice is not cosmetic — see
ROADMAP.md, "unresolved-target hub".

## `comment_entities_annotators.csv` — the annotated sample only

One row per (entity, annotator): `entity_id`, `comment_id`, `annotator_email`,
`is_abusive` (`YES`/`NO`/**`UNSURE`**), `entity_type`, `target_id`.
Three annotators per entity. They disagree on ~17% of entities. The adjudicated
label in `comment_entities.csv` is a *decision procedure applied to these votes*,
not an observation. In the real project this file exists for 610 comments and
the adjudicated one for 602.

## `annotation_selection.csv` — the annotated sample only

`comment_id`, `selection_stratum` — which stratum of the sampler pulled this
comment in. Keep it: it is the only record of *why* a comment is in the sample,
and every bias analysis needs it.

## `comment_labels_weak.csv`

Comment-level labels from two fine-tuned models. These are **not** the gold labels. In the v2 pipeline they are what selected
comments for annotation; the default the annotated sample sampler deliberately does **not**
use them.

| column | meaning |
|---|---|
| `qwen_abusive`, `llama_abusive` | bool, per model |
| `abusive_either`, `abusive_both` | bool |
| `abuse_priority` | `3`=both, `2`=qwen only, `1`=llama only, `0`=neither (real rule, `dataset_v2_20k/build_universe.py`) |
| `entity_count`, `n_words` | ints |

## `comments.csv`

`comment_id`, `subreddit`, `submission_id`, `parent_id`, `comment_text`,
`comment_score`, `author_username`, `author_id`, `comment_timestamp`.

`parent_id` is `t3_<submission_id>` (top-level, ~63%) or `t1_<comment_id>`
(a reply). This is the only source of user→user interaction.
From the medium dataset on, some rows have `author_username == "[deleted]"` and an empty
`author_id`. **Those are not one user.** See `load.handle_deleted_authors`.

## `submissions.csv`

`submission_id`, `subreddit`, `submission_title`, `submission_body`,
`submission_score`, `author_username`, `submission_url`, `submission_timestamp`,
`submission_kind` (`post_game_thread` / `discussion`), `game_id`,
`related_team_ids` (`|`-separated).

`game_id` is **empty** for discussion threads and for a small share of game
threads we could not link (6–9% from the medium dataset on — the real linker,
`sports_scripts/match_game_threads_to_results.py`, is heuristic and also fails).

## `games.csv`

`game_id`, `event_id`, `gender`, `season`, `date_utc`, `league_group`,
`team_home_id`, `team_away_id`, `home_team_name`, `away_team_name`,
`home_score`, `away_score`. Winner/loser/margin are derived in `load_dataset`.

## `players.csv` / `teams.csv` / `coaches.csv`

`player_id` = `{season}:{gender}:{team_id}:{player_slug}` — the real format.
Note it is **season-scoped**: the same human has a different `player_id` in a
different season, and a different one again if they transfer. That is a real
entity-resolution problem, not a synthetic artefact.

## `users.csv`

`author_id`, `author_username`, `home_team_id`, `followed_team_ids`.
The generator also assigns each user a behavioural *role* — how active they are,
who they pay attention to, how likely they are to be abusive. **That column is
withheld.** Your supervisor has it. Work out what the roles are from the data
first; then ask.
