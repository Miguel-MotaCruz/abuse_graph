# Research roadmap: ten phases

A **phase** is a research step. It is numbered. It says which node types, edge
types and attributes exist, and what question justifies them.

A **dataset** is a pile of rows. It has a word for a name (`toy`, `small`,
`medium`, `large`, `annotated_sample`) and never a number. See `DATASETS.md`.

A phase runs on whichever dataset suits it. Phase 1 runs on `toy` → `small` →
`medium`. Phase 6 needs `large`, because the annotated sample cannot support it.

**The governing rule: a phase does not add a node type until a question needs
it.** Adding `Game` in Phase 1 costs nothing to build and everything to reason
about.

---

## Summary

| phase | question | node types | edge types |
|---|---|---|---|
| **1** | Who targets whom, and do the users form groups? | `User`, `Comment`, `Target` | authored, targets |
| **2** | Which Phase 1 conclusions were small-sample artefacts? | — same — | — same — |
| **3** | What does aggregating cost us? | + `Submission` | + reply_to, in_thread, user→user (reply), user–user (co-target) |
| **4** | Is the abuse network structurally different? | — same — | abuse-only subgraph **+ a null model** |
| **5** | Does any of this change over time? | — same — | a sequence of windowed graphs |
| **6** | Do games and results move it? | + `Game`, `Team` | + played, thread_for |
| **7** | Does it survive contact with real data? | — same — | + pseudonymised ids |
| **8** | Is any of it statistically real? | no new graph | — |
| **9** | Do graph features help detection? | no new graph | — |
| **10** | Is a GNN justified? | typed, as Phase 3 | — |

---

## Phase 1 — construction, metrics, communities

**Runs on:** `toy` → `small` → `medium`  **Code:** you write it — `build_graph.py`

```
User  --authored-->  Comment  --targets(is_abusive)-->  Target
                        |
                        +----targets(is_abusive)----->  Target
```

Keeping `Comment` as a node is the point. A comment with three targets has three
outgoing edges and **they can carry different labels** — the same sentence can
insult one player and praise another. Go straight to `User → Target` and you can
never see that. In `toy`, 69 of 130 comments name more than one target and 12
carry mixed labels. Print those first.

Then collapse it to `User → Target` — by hand first — and answer:
*what can you no longer ask?*

**Target scope.** `toy` has only players. `small` adds teams. Only those two
resolve to an id, because only two master files exist. Coach mentions are 5.2%
of the real gold and have **no id at all** — there is no coach master file — so
they behave like any other unresolved target. There is also **no `player → team`
edge**: team membership is an attribute. The edge would put every pair of users
who mention different players on the same team two hops closer and make each
team a hub that quietly merges fanbases; you would then "discover" communities
the edge itself created.

**Attributes to compute** (none of them are stored in the data):

- *User* — `n_comments`, `n_interactions` (target mentions, which is larger),
  `n_abusive`, `abuse_rate`, `n_targets`, `n_abusive_targets`,
  `target_concentration` (Herfindahl or entropy), `first_seen`, `last_seen`,
  `n_threads`
- *Comment* — `submission_id`, `timestamp`, `n_targets`, `is_reply`. Note
  `n_targets` is a comment property and abuse is not; that contrast is the
  lesson.
- *Target* — `entity_type`, `team_id`, `n_distinct_users`, `n_abusive_users`,
  `n_interactions`, `abuse_share`, **`abuse_share_shrunk`** (a rate over n=3 is
  not comparable to one over n=300)
- *Edge, `Comment→Target`* — `is_abusive`, `entity_text`, `entity_id`
- *Edge, after collapsing* — `interaction_count` (= weight), `abusive_count`,
  `nonabusive_count`, `abuse_rate`, `first_interaction`, `last_interaction`,
  `span_days`, `n_distinct_threads`

**Not here:** games, time windows, user→user edges.

> **Trap.** 18% of real target mentions have no resolvable id. Key them by type
> — one `UNRESOLVED:referee` node — and every user who ever complained about a
> ref is two hops from every other. On `large` that decision alone took the
> user–user projection from ~0.5M to 1.1M edges. Try all three: drop them, one
> node per mention, or one node per type.

## Phase 2 — scale

Nothing new structurally: `medium` → `large`. The objective is to find which
Phase 1 conclusions were small-sample artefacts, and which code stops running.

## Phase 3 — representations and information loss

**New nodes:** `Comment`, `Submission`. **New edges:** reply_to, in_thread,
`User→User` (reply), `User–User` (co-target).

Four graphs from one interaction table:

| | what it is | on `large` |
|---|---|---|
| **A** event | loses nothing | 63,291 nodes / 182,756 edges |
| **B** user→target | the working graph, aggregated + weighted | 3,586 / 27,599 |
| **C1** reply | **observed** user→user interaction | 2,146 / 16,251 |
| **C2** co-target | **derived** projection; needs a degree discount | 2,418 / **1,105,695** |

C1 and C2 are not variants of one thing. One is observed, one is derived, and
the original project brief treated them as a single representation.

Related limitation: **the entity taxonomy has no `user` type**, so abuse aimed
at other Redditors is invisible to the gold layer. "Abusive reply" can only mean
"a reply whose comment abused *someone*", not "abuse aimed at the parent
author".

## Phase 4 — abuse-specific networks

B restricted to edges with `abusive_count > 0`, **plus a null model**.

The abuse graph is smaller and sparser by construction — that is arithmetic, not
a finding. To claim a structural difference, rewire B keeping every user's
out-degree and every target's in-degree (a bipartite configuration model), or
thin B by the global abuse rate, and compare against that.

New attributes: `is_persistent_abuser` (same target in ≥k windows),
`abuse_breadth`, `abuse_focus`.

## Phase 5 — temporal

A sequence `B_t`, one graph per window, with per-window versions of every
Phase 1 attribute. **Window length is a research question, not a constant** —
report at least two of 6h / 24h / 7d / event-anchored.

New quantities: node and edge churn between windows, community persistence
across windows, per-user activity and abuse trajectories.

## Phase 6 — games and results

**New nodes:** `Game`, `Team` as first-class. **New edges:** `Team→Game`,
`Submission→Game`. **New edge attributes on User→Target:** `hours_after_game`,
`user_follows_loser`, `margin`, `window` ∈ {pre, during, post}.

Constraints from the real data: 79.6% of submissions are game threads;
`game_id` is missing for discussion threads *and* for 6–9% of game threads
because the real linker is heuristic; scores give win, loss and margin directly.

There is something here to find: on `large`, the abuse rate within 8 hours of
a game a user's team lost differs from the rate outside that window. Whether the
difference survives a test with clustered standard errors is the interesting
part, not the raw gap.

## Phase 7 — real data

Same schema. Two things change:

1. **Pseudonymise `author_username` before anything else.**
2. `player_id` is season-scoped (`season:gender:team_id:slug`), so the same
   person is a different node in a different season, and a transfer makes them
   different again. Multi-season work needs a person-level id above it.

Order: one game → one team, one month → one season → everything.

## Phase 8 — statistics

No new graph. Hypotheses, tests, effect sizes, and honest treatment of the
selection bias in `DATASETS.md`.

## Phase 9 — detection baselines

No new graph. A feature matrix per unit of prediction — decide the unit first
(entity, comment, or user; they are different tasks). **Split by user**, not by
comment, or activity leaks between train and test.

Order: text-only → behavioural → graph → combined.

## Phase 10 — graph ML

Only if Phase 9 leaves something unexplained. Heterogeneous graph with typed
nodes and edges as in Phase 3A, features from Phases 1–6.
