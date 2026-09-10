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

You need Python 3.10 or newer.

```bash
python -m pip install -r requirements.txt
python load_data.py
```

If that prints a list of tables and three rows of data, you are ready.

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

## What to do, in order

Take your time. This is four to six weeks of work if you are learning Python
alongside it, and that is fine.

### Step 1 — Python, if you need it

If you are not comfortable with lists, dictionaries, loops and functions, do
this first and do not skip it:

- **Python for Everybody**, Dr. Charles Severance — <https://www.py4e.com>
  Free videos and a free book, written for people who are not programmers.
  Chapters 1–10. This is the best free Python course for a beginner, and it is
  not close.

Then, for the data handling:

- **Corey Schafer's pandas series** on YouTube — search "Corey Schafer pandas".
  The first five videos are enough. `pandas` is how you will touch every file
  in `data/`.

### Step 2 — see the thing before you build it

```bash
open interactive/toy.html      # or just double-click it
```

**Do the seven-step guided tour** in the sidebar, in order, and answer the
question each step asks *before* clicking to the next one. Write the answers
down. Some are harder than they look.

Then do the same with `interactive/small.html` and notice what changed.

### Step 3 — read

`TUTORIAL_GRAPHS.md`, sections 1 to 4. Do the exercises; the answers are
deliberately not in the file. Then read Phase 1 in `ROADMAP.md`, and skim
`SCHEMA.md` so you know what columns exist.

### Step 4 — build it

```bash
python build_graph.py
```

Read the output, then read the code, then do the TODOs at the bottom. You are
building the whole `toy` graph.

**Before you run your finished version, write down your prediction for how many
nodes and how many edges it will have.** If you are wrong, work out why before
you change anything.

### Step 5 — draw it

```bash
python plot_graph.py
```

Same deal: read, then do the TODOs. Compare what you get with
`reference/toy_graph_reference.png`. It will not be laid out identically — the
layout is random — but it should have the same shape and the same counts.

### Step 6 — measure it

`TUTORIAL_GRAPHS.md` sections 5 to 8: degree, centrality, why the clustering
coefficient here is exactly zero, projection, and communities.

By the end you should be able to answer, from the data and without being told:

- Who are the most active users? Are they the most abusive ones?
- Who gets targeted most? Are they the most abused?
- Do the users fall into groups? What is each group organised around?
- Is there anyone who does not fit any group?

Write your answers down **before** you ask your supervisor for the answer key.
It exists, and asking for it early wastes the exercise.

---

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
