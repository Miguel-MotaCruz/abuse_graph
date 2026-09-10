# Graphs, from scratch, using this project's data

For someone who has not written much code and has never met a graph. Work
through it in order. Every code block runs against `toy`, which is 130 comments
and small enough to print in full.

**Sections 0–4 are your first week** — about 1.5 hours of reading plus the
exercises. Stop at §5; centrality and communities come after you have built the
graph yourself.

Do not read ahead. Do the exercises. The answers to most of them are *not* in
this file, on purpose.

External resources are in §11, with honest time estimates.

---

## 0. Setup

```bash
uv sync
uv run python -c "import networkx; print(networkx.__version__)"
```

Every command in this file assumes `uv run` in front of it. For interactive
work, `uv run python` gives you a REPL with everything already importable.

```python
from load_data import load
d = load('toy')
for name, table in d.items():
    print(f"{name:22s} {len(table):>5} rows")
```

---

## 1. What a graph is

A graph is two things: a set of **nodes** and a set of **edges** joining pairs
of them. That is all. Everything else in this file is a consequence.

Notation you will see everywhere: `G = (V, E)`, where `V` is the set of nodes
(*vertices*) and `E` the set of edges. `|V|` means "how many nodes".

A graph is a *modelling choice*, not a property of the world. There is no
"the graph" of a Reddit thread. You decide what is a node and what is an edge,
and different decisions answer different questions. That decision is the single
most consequential thing you will do in this project, and §7 is about it.

**Directed vs undirected.** An edge either has a direction (A → B, "A wrote
this comment") or it does not (A — B, "A and B went to the same school").
Friendship is naturally undirected; authorship is naturally directed. Ours are
directed.

**Weighted vs unweighted.** A weight is a number on an edge: how many times, how
strongly, how recently. Our Phase 1 graph is unweighted — one edge per event —
and weights appear only after we aggregate in §7.

**Multigraph.** If A can be joined to B more than once, you either allow
parallel edges (a multigraph) or you collapse them into one edge with weight 2.
That collapse loses the *order* the events happened in. Remember that; it comes
back in §7.

### Try it

```python
import networkx as nx
G = nx.DiGraph()                 # directed
G.add_edge('anna', 'comment_1')
G.add_edge('comment_1', 'player_x')
print(G.number_of_nodes(), G.number_of_edges())
print(list(G.nodes), list(G.edges))
```

**Exercise 1.1.** Add a second comment by anna that also targets `player_x`.
Now `G.number_of_edges()` is 4. Suppose instead you wanted *one* edge
`anna → player_x` with weight 2. Write down one question you could still answer
with the first version that you could not answer with the second.

---

## 2. Our graph

```
user  --authored-->  comment  --targets-->  target
```

Three kinds of node, two kinds of edge. You build it yourself — that is what `build_graph.py` is for. Work through that
file before continuing here.

Two design decisions are already baked in, and both are arguable:

**(a) Comments are nodes.** They could have been edges — "anna targeted
player_x" — but the abuse label belongs to a (comment, target) pair, and a
comment naming three people can be abusive toward one and civil to the other
two. Make the comment an edge and that becomes unrepresentable.

```python
x = d["interactions"]
per_comment = x.groupby("comment_id").agg(
    n_targets=("entity_id", "size"),
    n_labels=("is_abusive", "nunique"))
mixed = per_comment[per_comment.n_labels > 1]
print(len(mixed), "comments carry different labels for different targets")
print(x[x.comment_id.isin(mixed.index)].head(10)
      [["comment_id", "entity_text", "is_abusive"]].to_string(index=False))
```

Read those rows. They are the justification for the whole design.

**(b) There is no player → team edge.** Team membership is stored as a node
*attribute*, not a link. If you added the edge, every pair of users who mention
different players on the same team would become two hops closer, each team
would become a hub, and you would later "discover" communities that the edge
itself created.

**Exercise 2.1.** Take three users. For each, list the players they target.
Now imagine player→team edges exist. Which pairs of users would become
connected that are not connected now?

### Node and edge attributes

Nodes and edges can carry data. Ours do:

```python
print(G.nodes['c_0000005'])                      # a comment
u = [n for n, k in G.nodes(data='kind') if k == 'user'][0]
print(list(G.out_edges(u, data=True))[:2])       # authored edges
c = list(G.successors(u))[0]
print(list(G.out_edges(c, data=True)))           # targets edges, with is_abusive
```

`is_abusive` is `YES` or `NO`. There is no third value: individual human
annotators may answer "unsure", but adjudication resolves every entity, so the
label you analyse is binary.

---

## 3. Degree, and why it is not one thing

The **degree** of a node is how many edges touch it. In a directed graph that
splits into **in-degree** (arriving) and **out-degree** (leaving).

```python
print(G.out_degree(u), G.in_degree(u))
```

For a user: out-degree is comments written, in-degree is **always 0** — users
only emit. For a comment: in-degree is **always 1** (its author). For a target:
in-degree is how often it was mentioned, out-degree **always 0**.

That is worth pausing on. Two of those three columns carry no information at
all, and they will still appear in every table you produce. A metric being
*computable* is not the same as it being *informative*.

**Degree distribution.** Plot degree against how many nodes have it. Real social
graphs are heavy-tailed: most nodes have a small degree and a few have an
enormous one. Our data is calibrated to a real corpus where the top 1% of
authors write 28% of the comments.

```python
import collections
users = [n for n, k in G.nodes(data='kind') if k == 'user']
print(sorted((G.out_degree(x) for x in users), reverse=True))
```

**Exercise 3.1.** Compute the mean and the median of that list. They differ a
lot. Which one would you put in a paper, and what would the other one tell a
reader that the first does not?

---

## 4. Paths, distance, components

A **path** is a sequence of edges you can walk along. **Distance** between two
nodes is the length of the shortest path. **Diameter** is the largest distance
in the graph.

In our graph every user→user path looks like

```
user → comment → target ← comment ← user
```

so two users who share a target are **four** steps apart, and two users who
share nothing are not connected at all. That single fact explains most of what
happens later, including why community detection here is really about shared
targets.

A **connected component** is a set of nodes you can reach from one another. If
your graph has several, most global metrics either break or silently apply to
one component only.

```python
U = G.to_undirected()
comps = sorted(nx.connected_components(U), key=len, reverse=True)
print("components:", len(comps), "sizes:", [len(c) for c in comps])
```

**Exercise 4.1.** Look at the small components. Who is in them, and why are
they cut off from the rest? (This is not a bug in the data.)

---

## 5. Centrality: five answers to "who matters?"

Centrality is any attempt to score nodes by importance. There are several
because "important" means different things.

You compute all of them with one line each. `G` is the graph you built in
`build_graph.py`; `U` is the same graph with the directions removed, which some
of these need.

```python
import networkx as nx
import pandas as pd

U = G.to_undirected()

m = pd.DataFrame({
    "kind":        pd.Series(dict(G.nodes(data="kind"))),
    "label":       pd.Series(dict(G.nodes(data="label"))),
    "out_degree":  pd.Series(dict(G.out_degree())),
    "in_degree":   pd.Series(dict(G.in_degree())),
    "degree":      pd.Series(dict(U.degree())),
    "betweenness": pd.Series(nx.betweenness_centrality(U)),
    "closeness":   pd.Series(nx.closeness_centrality(U)),
    "eigenvector": pd.Series(nx.eigenvector_centrality(U, max_iter=1000)),
    "pagerank":    pd.Series(nx.pagerank(G)),
    "clustering":  pd.Series(nx.clustering(U)),
})

print(m[m.kind == "user"].nlargest(8, "degree").to_string())
```

The vocabulary, which you will hear constantly:

- **Degree** — how many edges touch a node. The cheapest measure of importance
  and usually the first thing to look at. Split into **in-degree** (edges
  arriving) and **out-degree** (edges leaving) when the graph is directed.
- **Weighted degree**, also called **strength** — the same thing but summing
  edge weights instead of counting edges. Ours are unweighted, so strength
  equals degree until you aggregate in §7.
- **Betweenness centrality** — what share of all shortest paths in the graph run
  through this node. High betweenness means you are a **bridge**: delete the
  node and parts of the graph fall away from each other. Expensive: roughly
  (nodes × edges), so it is the first thing that becomes unaffordable at scale.
- **Closeness centrality** — the inverse of your average distance to everyone
  else. "How near am I to the whole graph?"
- **Eigenvector centrality** — you are important if your neighbours are
  important. Defined circularly and solved as an eigenvector problem, which is
  where the name comes from.
- **PageRank** — imagine a walker following edges at random, occasionally
  teleporting to a random node. PageRank is where it spends its time. This is
  the algorithm Google was built on.
- **Clustering coefficient** — of all the pairs of my neighbours, how many are
  connected to each other? "Do my friends know each other?" See §6.

Now the part that matters more than any of the definitions. Run this:

```python
print(m[m.kind == "user"].pagerank.describe())
print(m[m.kind == "comment"].in_degree.unique())
print(m.clustering.unique())
```

**Three of the numbers you just computed are meaningless on this graph:**

- **User PageRank is constant.** Users are pure *sources* in a directed
  user→comment→target graph — nothing ever points at them — so they receive
  only the teleport mass. Ranking users by PageRank ranks the damping factor.
- **Comment in-degree is always 1.** Every comment has exactly one author.
- **Clustering is exactly 0 for every node**, and it is forced by the shape of
  the graph rather than being a fact about the data. §6.

A metric being *computable* is not the same as it being *informative*. Getting
this distinction is most of the skill.

**Exercise 5.1.** Rank users by degree, then by betweenness. The orders differ.
Pick one user who moves a lot and explain, from the graph, why.

**Exercise 5.2.** The highest-degree user has an abuse rate near zero. Find them.
Then find the most abusive user. What does that tell you about using centrality
as a proxy for harm?

---

## 6. Triangles, clustering, and bipartite graphs

**Clustering coefficient** asks: of all the pairs of my neighbours, how many are
connected to each other? It measures "do my friends know each other".

On our graph it is **exactly zero everywhere**, and there are **zero triangles**.
Verify it, then work out why before reading on.

```python
print(sum(nx.triangles(U).values()) // 3, nx.average_clustering(U))
```

The reason: our graph is **tripartite**. Every edge joins two *different* kinds
of node (user–comment, or comment–target). A triangle needs three mutually
connected nodes, which would require an edge between two nodes of the same kind.
There are none. So the zero is forced by the shape of the graph and tells you
nothing about the data.

A **bipartite** graph has two kinds of node and edges only between kinds — a
users-and-targets graph, for instance. Bipartite graphs are everywhere
(customers–products, authors–papers) and they have their own versions of the
standard metrics, because the standard ones misbehave. If you want a clustering
coefficient on one, look up **Latapy et al. (2008)**.

**Exercise 6.1.** Name one other metric you would expect to misbehave on a
bipartite graph, and say what you would use instead.

---

## 7. Projection: making a graph smaller, and what it costs

Our graph has 130 comment nodes and 15 users. If the question is "who targets
whom", the comments are in the way. So **aggregate** them out:

```python
import collections

H = nx.DiGraph()                     # the projected graph
counts = collections.Counter()       # (user, target) -> how many times
abusive = collections.Counter()      # (user, target) -> how many were abusive

for user in [n for n, k in G.nodes(data="kind") if k == "user"]:
    for _, comment in G.out_edges(user):
        for _, target, edge in G.out_edges(comment, data=True):
            counts[(user, target)] += 1
            abusive[(user, target)] += (edge["is_abusive"] == "YES")

for (user, target), n in counts.items():
    H.add_edge(user, target,
               weight=n,
               interaction_count=n,
               abusive_count=abusive[(user, target)],
               abuse_rate=abusive[(user, target)] / n)

print(G.number_of_nodes(), "->", H.number_of_nodes(), "nodes")
print(G.number_of_edges(), "->", H.number_of_edges(), "edges")
print(list(H.edges(data=True))[0])
```

This is a **projection**: a smaller graph derived from a bigger one. Notice the
edges are now **weighted** — that is what aggregation buys you, and it is why
"weighted degree" finally means something different from "degree".

**What you lost.** Which comment. Whether two targets were named in the *same*
comment. The order of events within a pair. Ten interactions in one night now
look like ten spread over four months — unless you also carry the first and
last timestamp, which is why real pipelines do.

Do the collapse by hand for one user, on paper, and check you get the same
numbers.

### The dangerous projection

A **user–user** projection connects two users if they share a target. It sounds
harmless and it is not: a single target mentioned by `k` users creates
`k(k-1)/2` edges. One popular player wires half the graph into a **clique** (a
set of nodes where everyone is connected to everyone), and any community you
then detect is partly "people who talked about that player".

```python
import itertools

users_of = collections.defaultdict(set)
for user, target in H.edges():
    users_of[target].add(user)

naive = collections.Counter()      # how many targets do these two share?
newman = collections.Counter()     # ... discounted by how popular each target is
for target, users in users_of.items():
    k = len(users)
    if k < 2:
        continue
    for a, b in itertools.combinations(sorted(users), 2):
        naive[(a, b)] += 1
        newman[(a, b)] += 1 / (k - 1)

print(len(naive), "user-user edges from", H.number_of_nodes(), "nodes")
print("heaviest naive :", naive.most_common(3))
print("heaviest newman:", sorted(newman.items(), key=lambda kv: -kv[1])[:3])
```

Same edges, different **weights**. The **Newman (2001)** discount gives each
shared target a weight of `1/(deg(t) - 1)`, so a target everybody mentions
contributes almost nothing and a target two people share contributes a lot.
Community detection optimises over weights, so these two graphs can give
different answers while being identical in any node or edge count.

**Exercise 7.1.** At `large` the naive projection has over a million
edges against 28,000 for user→target. Predict which one takes longer to run
betweenness on, then look up the complexity and check.

---

## 8. Communities

A **community** is, loosely, a group of nodes with more connections inside the
group than outside. "Loosely" is doing a lot of work: there is no single
agreed definition, and different algorithms optimise different things.

**Modularity** is the most common objective. It compares the number of edges
inside your proposed groups against how many you would expect *if the edges were
rewired at random, keeping every node's degree the same*. That comparison
baseline is called a **null model**, and modularity's null model assumes an
undirected, unipartite graph. Ours is neither. Keep that in mind.

**Louvain** is a fast greedy algorithm for maximising modularity. **Leiden**
(Traag et al. 2019) fixes a real defect in Louvain — it can return communities
that are internally disconnected — and should be your default in new work.

Run it on the **full** graph, without collapsing anything:

```python
import networkx as nx
part = nx.community.louvain_communities(G.to_undirected(), resolution=0.5, seed=0)
part = {n: i for i, group in enumerate(part) for n in group}   # node -> community

users = [n for n, k in G.nodes(data='kind') if k == 'user']
import collections
print(collections.Counter(part[u] for u in users))
```

Now summarise each community yourself: how many users, how many interactions,
what fraction abusive, and which targets it talks about most.

Comments and targets get community labels too; we read off the user nodes,
because the question is about people. Two users are connected only through the
targets they share, so **the communities are induced by shared targets**. That
is the mechanism. Knowing the mechanism is the difference between using a tool
and being used by one.

### The distinction that matters most

Only **structure and edge weights** go into the algorithm. `is_abusive`,
`abuse_rate`, team, entity type are used **afterwards**, to describe what came
out.

If you fed abuse into detection and then reported that the communities differ in
abuse, you would have discovered your own input. Write down, every time, which
attributes went in and which came after.

### Three things to check before believing any partition

```python
# 1. Rerun Louvain with several different seeds and compare the partitions.
# 2. Rerun it at resolution 0.3, 0.5, 1.0 and 2.0 and count the communities.
# 3. Count how many targets are talked about by users from more than one
#    community, and how much of the shared-target weight your partition cuts
#    through. You will have to write these; that is the exercise.
```

1. **Stability.** Louvain is stochastic — it picks a random starting order. If
   different seeds give different partitions, any story about one run is a
   story about that seed.
2. **Resolution.** A parameter almost nobody reports. Sweep it and watch the
   number of communities and the agreement with truth both move a long way.
3. **Overlap.** Count the **contested targets** — the ones discussed by users
   from more than one community — and the share of shared-target weight your
   partition cuts through. If almost nothing is contested, your "communities"
   are just separate components and the algorithm did no work. (The interactive
   view highlights contested targets at step 5, so you can check your count.)

**A high modularity score is not evidence that the communities mean anything.**
The test is whether the groups differ in something you did not feed in: do they
talk about different people? Read the `top_targets` column.

**Exercise 8.1.** This is synthetic data, so an answer key exists — your
supervisor has it. **Write down your answer first**: how many groups of users do
you think there are, who is in each, and what is each group organised around.
Then ask for the key.

The comparison is usually made with the **Adjusted Rand Index**: agreement
between two partitions, corrected for chance, 1.0 identical and 0.0 no better
than random.

Then the real question — **on real data there is no key.** Write down three
things you could check instead, and be honest about how much weaker each one
is.

---

## 9. Seeing it

```bash
open interactive/toy.html          # macOS;  on Windows just double-click it
```

The interactive view has a seven-step guided tour. Do the steps in order and
answer the question each one asks before moving on. It also lets you switch node
types off, show only abusive edges, isolate a community, and highlight lone
wolves and contested targets — the abuse rate in the side panel updates for
whatever is visible.

One caution about layouts. A force-directed layout (the standard "spring"
layout) pushes connected nodes together and unconnected nodes apart, which makes
it a *continuous relaxation of roughly what modularity optimises*. So if a graph
has community structure, the plain layout already shows it and the colours will
agree. That agreement is a sanity check, not a discovery — and it means a
picture can never be your evidence for a community.

**Exercise 9.1.** In the interactive view, hide all comment nodes. The picture
gets much clearer. What did you lose the ability to see?

---

## 10. What comes next

`ROADMAP.md` lays out the whole project. Phase 1 is what this tutorial covers.
After it: scale up (the medium dataset, the large dataset), study what projection costs you, build
abuse-only graphs and compare them against a proper null model, add time, add
games, then real data.

Two ideas worth meeting early because they will save you from a wrong result:

- **Null models.** "The abuse network is sparser than the interaction network"
  is not a finding — it is arithmetic. To claim a structural difference you need
  to compare against a random graph that preserves what you are not interested
  in (usually every node's degree) and destroys what you are.
- **Small samples.** An abuse rate of 1.0 over 3 interactions is not higher than
  0.4 over 300. Search terms: *empirical Bayes shrinkage*, *Wilson interval*.

---

## 11. Free resources, with honest time estimates

The times are what it actually takes, not what the marketing says. Only the
first two are for your first week.

### Now, if you need them

| | time | what it is |
|---|---|---|
| **Kaggle "Python"** — <https://www.kaggle.com/learn/python> | ~5 h | 7 short lessons, runs in your browser, nothing to install. The fastest honest route from zero to writing loops and functions. Skip it if you can already do that. |
| **NetworkX tutorial** — <https://networkx.org/documentation/stable/tutorial.html> | ~45 min | The official walkthrough of the library you are using. Type the examples in; reading it passively is worth a quarter as much. |

### Soon, at your own pace

| | time | what it is |
|---|---|---|
| **Kaggle "Pandas"** — <https://www.kaggle.com/learn/pandas> | ~4 h | Same format. `pandas` is how you touch every file in `data/`. Do this once the graph code starts feeling like the easy part. |
| **Network Science**, Barabási — <http://networksciencebook.com> | ~3 h for ch. 1–2 | The whole book, free, online, beautifully illustrated. Chapters 1 and 2 are your foundation and assume very little maths. The best single thing to read on networks. Chapters 3–4 (scale-free networks) when you get to degree distributions. |
| **Corey Schafer's pandas videos** on YouTube | ~2 h for the first 5 | If you would rather watch than click through Kaggle. Same material. |

### Later, when a specific problem sends you there

- **Networks, Crowds, and Markets** — Easley & Kleinberg,
  <https://www.cs.cornell.edu/home/kleinber/networks-book/>. Free PDF. Strong on
  the *social science* of networks — homophily, weak ties, community structure —
  with almost no linear algebra. Chapters 1–5, a few hours each. Read it when
  you start asking what a community *means*.
- **Traag, Waltman & van Eck (2019), "From Louvain to Leiden"** —
  <https://www.nature.com/articles/s41598-019-41695-z>. ~30 min. Short and
  readable, and the reason not to default to Louvain.
- **Mark Newman, "Networks: An Introduction"**. Not free. The clearest treatment
  of centrality and community detection anywhere. Find a library copy when §8
  becomes real work.
- **Latapy, Magnien & Del Vecchio (2008)** on bipartite metrics — when §6
  becomes a problem you actually have.
- **D3 force-directed example** —
  <https://observablehq.com/@d3/force-directed-graph>. 15 minutes of dragging
  nodes around builds better intuition for what a layout *is* than an hour of
  reading.

### Do not start here

Anything titled "graph neural networks", "node2vec", or "graph embeddings", and
the second half of Stanford's CS224W. They are the last phase of this project
and they will make more sense once you have a question that simpler methods
cannot answer. (CS224W lectures 1–3 are good on fundamentals if you like
lectures — but stop there.)

## Checklist

By the end you should be able to explain, without notes:

- [ ] what a node and an edge are, and why the choice is not obvious here
- [ ] why the comment is a node and not an edge
- [ ] why there is no player→team edge
- [ ] why in-degree is useless for users and comments in this graph
- [ ] why the clustering coefficient is exactly zero, without looking it up
- [ ] what modularity compares against, and why that matters here
- [ ] which attributes went into community detection and which came after
- [ ] what a user–user projection creates out of one popular target
- [ ] why a picture is not evidence for a community
- [ ] what you lost when you collapsed user→comment→target to user→target
