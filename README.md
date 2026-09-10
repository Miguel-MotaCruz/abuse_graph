# Graph analysis of abusive behaviour in sports discussion — starting point

Everything you need for the first few weeks. Read this page top to bottom before
you touch anything else.

## What the project is

We want to understand the *structure* of abusive behaviour in online sports
discussion: who is abusive, whom they target, whether abusive users cluster
together, whether some focus on one person and others spray widely, and whether
any of it responds to what happens in the games.

Those are questions about **relationships between things**, not about individual
comments. That is why the answer is a graph.

Eventually this runs on a real corpus of hundreds of thousands of Reddit
comments with human abuse annotations. You will not touch that for a while. You
will work on synthetic data that has the same shape.

**Everything in `data/` is invented.** No real person, team, comment or label
appears in it. The names are made up. Only the *statistical shape* — how often
people post, how often abuse occurs, how many people a comment mentions — is
copied from the real corpus.

---

## Setup

This project uses **uv**, which installs Python and every dependency for you.
You do not need to know what a virtual environment is yet.

Install uv once (macOS / Linux):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

On Windows, in PowerShell:

```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Then, in this folder:

```bash
uv sync            # installs Python 3.13 and the four packages. Once.
uv run python load_data.py
```

If that prints a list of tables and three rows of data, you are ready.

**From now on, put `uv run` in front of every python command.** That is the
whole trick: `uv run python build_graph.py`, not `python build_graph.py`. It
guarantees you are using this project's packages and not something else on your
machine.

---

## What is here

| | |
|---|---|
| `TUTORIAL_GRAPHS.md` | **Graph theory from scratch, using this data.** Your main reading. |
| `ROADMAP.md` | Where the project is going, in ten phases. Read Phase 1 now, skim the rest. |
| `SCHEMA.md` | Every column in every file, and what it means. |
| `load_data.py` | Loads a dataset. **Finished** — read it, don't change it. |
| `build_graph.py` | **Unfinished on purpose.** Shows you how to add nodes and edges. You write the rest. |
| `plot_graph.py` | **Unfinished on purpose.** Shows you how to draw them. You write the rest. |
| `interactive/toy.html` | The finished toy graph, explorable in a browser, with a seven-step tour. |
| `interactive/small.html` | The same for the small dataset. |
| `reference/toy_graph_reference.png` | What your finished toy graph should look like. |
| `data/toy/`, `data/small/` | The two datasets you will work with. |

---

## The one thing to understand before you write any code

**The unit of analysis is not the comment.** It is the pair
**(comment, target)** — one row of `comment_entities.csv`.

A comment can name three people and be abusive toward only one of them. The
human annotators attached the label to a specific *target inside* a comment, so
that is where it lives here too. In `toy`, **13 of the 130 comments carry
different labels for different targets in the same comment**.

If you write `df.groupby('comment_id')` and treat abuse as a property of the
comment, every number you produce afterwards will be quietly wrong.

That is why the graph looks like this:

```
user  --authored-->  comment  --targets(is_abusive)-->  target
                        |
                        +----targets(is_abusive)----->  target
```

Three kinds of node, two kinds of edge, and the label sits on the second kind
of edge.

---

## This week

About **6 hours** if you can already write a Python loop, **11** if you cannot.
Do them in this order. If you run out of time, stop where you are and tell me
where that was — that is useful information, not a failure.

### 1. Set up and check it works — 15 min

`uv sync`, then `uv run python load_data.py`. If it prints tables, you are done.

### 2. Explore the finished graph — 30 min

Open `interactive/toy.html` (double-click it). **Do the seven-step guided tour
in the sidebar, in order.** Each step asks a question. Write your answer down
*before* clicking next. Then open `interactive/small.html` and notice what
changed.

This is the most valuable 30 minutes of the week. Do not skip it.

### 3. Read — 1.5 hours

- the rest of this README, properly
- `TUTORIAL_GRAPHS.md` **sections 0 to 4 only** (setup, what a graph is, our
  graph, degree, paths and components). Do the exercises as you go.
- `SCHEMA.md` — skim it, so you know what columns exist. Come back to it
  constantly.

Stop at section 5. Centrality and communities are next week.

### 4. Python, only if you need it — 5 hours

If you cannot comfortably write a `for` loop over a list, or use a dictionary,
do this before step 5:

- **Kaggle "Python"** — <https://www.kaggle.com/learn/python> — 7 short lessons,
  about 5 hours, free, runs in your browser with nothing to install.

That is the fastest honest route from zero to enough. If you already know this,
skip it.

### 5. The NetworkX tutorial — 45 min

<https://networkx.org/documentation/stable/tutorial.html>

Read it with `uv run python` open in another window and type the examples in.
Reading it without typing is worth about a quarter as much.

### 6. Build the graph — 2 hours

```bash
uv run python build_graph.py
```

Read the output, then read the file, then do **TODOs 1 and 2** at the bottom.
(3, 4 and 5 are for next week.)

**Before running your finished version, write down your prediction for how many
nodes and how many edges it will have.** If you are wrong, work out why before
changing anything. Bring your prediction and the real number to our next
meeting.

### 7. Draw it — 1.5 hours

```bash
uv run python plot_graph.py
```

Same deal: read, then do **TODOs 1, 2 and 3**. Compare with
`reference/toy_graph_reference.png`. It will not be laid out identically — the
layout is random — but it should have the same shape and the same counts.

### Bring to the next meeting

1. Your seven answers from the tour.
2. Your node/edge prediction, and the real number.
3. Your version of `build_graph.py` and `plot_graph.py`.
4. Your PNG of the whole toy graph.
5. **A list of things that surprised you.** Written down before you explained
   them away. This is the item I care about most.

---

## After this week

Not now. Here so you can see where it goes.

- `TUTORIAL_GRAPHS.md` §5–8: centrality, why the clustering coefficient here is
  exactly zero, projection, and communities. The rest of the TODOs in both
  scripts.
- Then the four questions the whole first phase is aiming at:
  - Who are the most active users? Are they the most abusive ones?
  - Who gets targeted most? Are they the most abused?
  - Do the users fall into groups? What is each group organised around?
  - Is there anyone who does not fit any group?
- **Background reading, at your own pace, not this week:**
  [*Network Science*](http://networksciencebook.com) by Barabási, chapters 1–2.
  Free, online, well illustrated. About 3 hours. The best single thing to read
  on networks, but it is not urgent.

There is an answer key for the questions above. Write your answers down before
you ask for it, or you waste the exercise.

## Things that will save you time

- **Print things.** `df.head()`, `df.shape`, `df.columns`, `df['col'].value_counts()`.
  Half of data work is looking at what you actually have.
- **The toy dataset is small enough to read in full.** 130 comments. When
  something surprises you, go and find the actual rows.
- **Never conclude anything from `toy`.** With 15 users every number is noise.
  It exists so you can check your code against something you can eyeball. Any
  finding has to be checked on `small`.
- **Write down what surprised you**, before you explain it away. That list is
  the most valuable thing you will produce in the first month.
- **`data/medium`, `data/large` and `data/annotated_sample` are not in this
  repository yet.** Ask when you get there.

## If you get stuck

Bring three things: what you expected, what happened, and the shortest piece of
code that shows the difference. That is not just etiquette — assembling those
three things solves the problem about half the time.
