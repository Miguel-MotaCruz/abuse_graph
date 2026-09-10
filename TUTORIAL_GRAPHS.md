# Graphs, from scratch, using this project's data

For someone who has not written much code and has never met a graph. Work
through it in order. Every code block runs against `toy`, which is 130
comments and small enough to print in full.

You will need about four sessions of two hours. Do not read ahead; do the
exercises. The answers to most of them are *not* in this file, on purpose.

**External resources are at the end.** Read §11 before you start §1 if you
prefer video and lectures to reading.

---

## 0. Setup

```bash
python -m pip install -r requirements.txt
python -c "import networkx; print(networkx.__version__)"
```

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

Centrality is any attempt to score nodes by importance. There are many because
"important" means different things. Compute them:

```python
from metrics import node_metrics, metric_notes
m = node_metrics(G)
print(m[m.kind == 'user'].nlargest(8, 'degree')
      [['label','degree','interactions','abusive_out','abuse_rate',
        'betweenness','closeness','pagerank']].to_string())
```

- **Degree** — how many connections. Cheap, and usually the first thing you
  should look at.
- **Betweenness** — what share of all shortest paths run through you. High
  betweenness means you are a bridge: remove the node and parts of the graph
  fall away from each other. Expensive to compute (roughly nodes × edges).
- **Closeness** — how near you are to everyone else on average.
- **Eigenvector centrality** — you are important if your neighbours are
  important. Defined recursively; solved as an eigenvector problem.
- **PageRank** — a random walker following edges, restarting occasionally. Where
  does it spend its time?

Now the important part. Run this:

```python
print(m[m.kind=='user'].pagerank.describe())
print(m[m.kind=='comment'].in_degree.unique())
print(m.clustering.unique())
```

Three of the numbers you just computed are degenerate on this graph:

- **User PageRank is constant.** Users are pure sources in a directed
  user→comment→target graph, so they receive nothing but the restart mass.
  Ranking users by PageRank ranks the damping factor.
- **Comment in-degree is always 1.** Every comment has exactly one author.
- **Clustering coefficient is exactly 0 for every node.** See §6.

`metric_notes()` gives, for each metric, what it measures, which node types it
applies to, whether it is valid here, and its limitations. Read it.

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
whom", the comments are in the way. So aggregate:

```python
from graph import build_graph
from graphs import build_user_target      # user -> target, weighted
H = build_user_target(d)
print(H.number_of_nodes(), H.number_of_edges())
print(list(H.edges(data=True))[0])
```

Each edge now carries `interaction_count`, `abusive_count`, `abuse_rate`,
`first_interaction`, `last_interaction`. This is a **projection**: a smaller
graph derived from a bigger one.

**What you lost.** Which comment. Whether two targets were named in the *same*
comment. The order of events within a pair. Ten interactions in one night now
look much like ten spread over four months (partly recoverable from
first/last, not fully).

Do the collapse by hand once, for one user, and check you get the same numbers.

### The dangerous projection

A **user–user** projection connects two users if they share a target. It sounds
harmless and it is not: a single target mentioned by `k` users creates
`k(k-1)/2` edges. One popular player wires half the graph into a clique, and
any community you then detect is partly "people who talked about that player".

```python
from graphs import build_user_projection
P1 = build_user_projection(d, weight='count')     # naive
P2 = build_user_projection(d, weight='newman')    # degree-discounted
print(P1.number_of_edges(), P2.number_of_edges())     # same edges...
print(sorted((e['weight'] for *_ , e in P1.edges(data=True)), reverse=True)[:5])
print(sorted((e['weight'] for *_ , e in P2.edges(data=True)), reverse=True)[:5])
```

Same edges, different **weights**. The Newman (2001) discount gives each shared
target `t` a weight of `1/(deg(t) - 1)`, so a target everybody mentions
contributes almost nothing and a target two people share contributes a lot.
Community detection optimises over weights, so these two graphs can give
different answers while looking identical in any node/edge count.

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

## 11. The best free resources

Ranked for someone in your position. You do not need all of them.

### Start here

**Network Science — Albert-László Barabási.** <http://networksciencebook.com>
The whole book, free, online, beautifully illustrated. Chapters 1–4 (graph
theory, random networks, the scale-free property, the Barabási–Albert model) are
exactly your foundation and assume very little maths. This is the single best
free resource on this list; if you read one thing, read this.

**NetworkX tutorial.** <https://networkx.org/documentation/stable/tutorial.html>
Half an hour. The official walkthrough of the library you are using. Do it with
a REPL open.

### Lectures, if you prefer watching

**Stanford CS224W — Machine Learning with Graphs** (Jure Leskovec). Lecture
videos free on YouTube, slides at <https://web.stanford.edu/class/cs224w/>.
Lectures 1–3 cover graph fundamentals and node features; the later half is
graph neural networks, which is Phase 10 territory — do not start there.

**Networks, Crowds, and Markets — Easley & Kleinberg.**
<https://www.cs.cornell.edu/home/kleinber/networks-book/>
Free PDF. Strong on the *social science* of networks — homophily, strong and
weak ties, community structure — with almost no linear algebra. Chapters 1–5.

### Reference, for when you need the details

**Mark Newman, "Networks: An Introduction".** The standard textbook. Not free,
but the chapters on centrality and community detection are the clearest
treatment anywhere. Worth finding a library copy when you start §8 seriously.

**Traag, Waltman & van Eck (2019), "From Louvain to Leiden".**
<https://www.nature.com/articles/s41598-019-41695-z> — short, readable, and the
reason you should not default to Louvain.

**Latapy, Magnien & Del Vecchio (2008)**, on bipartite network metrics — read it
when §6 becomes a problem you actually have.

### Play

**D3 force-directed examples** — <https://observablehq.com/@d3/force-directed-graph>
Drag nodes around and watch the layout respond. Fifteen minutes of this builds
better intuition for what a layout *is* than any amount of reading.

### Skip for now

Anything titled "graph neural networks", "node2vec", or "graph embeddings". They
are Phases 9–10 and they will make more sense once you have a question that
simpler methods cannot answer.

---

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
