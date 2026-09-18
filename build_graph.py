"""EXAMPLE: building a graph by hand, with three rows of data.

This file is DELIBERATELY UNFINISHED. It shows you the moves; you write the
loop. Run it as it is first, read the output, then do the TODO at the bottom.

    python build_graph.py
"""
import networkx as nx

from load_data import load


# ===========================================================================
# PART 1 -- the moves, on three rows we type out by hand
# ===========================================================================
#
# The graph we are building has THREE kinds of node and TWO kinds of edge:
#
#       user  --authored-->  comment  --targets-->  target
#
# and the abuse label lives on the `targets` edge, NOT on the comment. A
# comment that names two people has two `targets` edges, and they can carry
# different labels. Watch for that below.

G = nx.DiGraph()          # DiGraph = directed graph: edges have a direction

# --- a node is just a name, plus any attributes you feel like attaching ----
# These are real rows: comment c_0000030 in the toy dataset. Go and look at it.
BENNETT = "2025-2026:men:men_KIRK_kirkmont-state-ravens:bennett-whitlock"
XAVIER = "2025-2026:men:men_KING_kingsmoor-poly-ironmen:xavier-duvalier"

G.add_node("u_000001", kind="user", label="glasscleaner_watcher252")
G.add_node("c_0000030", kind="comment")
G.add_node(BENNETT, kind="player", label="Bennett Whitlock")
G.add_node(XAVIER, kind="player", label="Xavier Duvalier")

# --- an edge joins two nodes. It can carry attributes too ------------------
G.add_edge("u_000001", "c_0000030", kind="authored")

G.add_edge("c_0000030", BENNETT, kind="targets", is_abusive="NO")
G.add_edge("c_0000030", XAVIER, kind="targets", is_abusive="YES")
#                                               ^^^^^^^^^^^^^^^^
# ONE comment. TWO targets. DIFFERENT labels. 13 of the 130 comments in `toy`
# look like this. If you had made the comment an edge instead of a node, or
# stored `is_abusive` on the comment, this would be unrepresentable.

# If you add a node that already exists, networkx updates it instead of
# duplicating it. That is very convenient: you can add the author on every
# single row without worrying about whether you have seen them before.

print("PART 1 -- built by hand")
print("  nodes:", G.number_of_nodes(), " edges:", G.number_of_edges())
print("  node data:", G.nodes["u_000001"])
print("  edge data:", G.edges["c_0000030", XAVIER])
print()

# --- reading things back out ----------------------------------------------
print("  everything u_000001 wrote:", list(G.successors("u_000001")))
print("  everything c_0000030 targets:", [G.nodes[n]["label"] for n in G.successors("c_0000030")])
print("  out-degree of the user:", G.out_degree("u_000001"))
print("  in-degree of the user:", G.in_degree("u_000001"), " <-- always 0. why?")
print()

# --- selecting nodes by kind ----------------------------------------------
users = [n for n, k in G.nodes(data="kind") if k == "user"]
players = [n for n, k in G.nodes(data="kind") if k == "player"]
print("  users:", users)
print("  players:", len(players))
print()


# ===========================================================================
# PART 2 -- the same three rows, taken from the actual data
# ===========================================================================
d = load("toy")
x = d["interactions"]

print("PART 2 -- the entire real interactions table")
print(x[["comment_id", "author_id", "author_username", "target_id",
         "entity_text", "entity_type", "is_abusive"]].to_string(index=False))
print()

G2 = nx.DiGraph()
for row in x.itertuples(index=False):
    # Each row is one (comment, target) pair, so each row gives us:
    #   - the author node          (may already exist -- fine)
    #   - the comment node         (may already exist -- fine)
    #   - the target node
    #   - an `authored` edge and a `targets` edge
    G2.add_node(row.author_id, kind="user", label=row.author_username)
    G2.add_node(row.comment_id, kind="comment")
    G2.add_node(row.target_id, kind="player", label=row.entity_text)
    G2.add_edge(row.author_id, row.comment_id, kind="authored")
    G2.add_edge(row.comment_id, row.target_id,
                kind="targets", is_abusive=row.is_abusive)

print("  from all rows:", G2.number_of_nodes(), "nodes,", G2.number_of_edges(), "edges")
#print("  (not 3 x 4 = 12 nodes -- why not?)")
print()


# ===========================================================================
# TODO -- your turn
# ===========================================================================
#
# 1. Change `.head(3)` to the whole table and build the graph for all of `toy`.
#    Put it in a function `build(d)` that takes the loaded data and returns G.
#
def build(d):
    G3 = nx.DiGraph()
    for row in d["interactions"].itertuples(index=False):
        G3.add_node(row.author_id, kind="user", label=row.author_username)
        G3.add_node(row.comment_id, kind="comment")
        G3.add_node(row.target_id, kind="player", label=row.entity_text)
        G3.add_edge(row.author_id, row.comment_id, kind="authored")
        G3.add_edge(row.comment_id, row.target_id, kind="targets", is_abusive=row.is_abusive)
    return G3
#
# 2. Before you run it, WRITE DOWN your prediction: how many nodes, how many
#    edges? You know how many users, comments and targets there are -- run
#    load_data.py to remind yourself. Then run it and see if you were right.
#    If you were wrong, work out why before reading on.
# 
# i was incredibly wrong. i predicted 3 nodes and 2 edges, but the actual output was 166 nodes and 350 edges. i said 3 and 2
# respectively because i was thinking about the TYPES of nodes and edges, not the actual number of them. it makes sense now 
# why each number is what it is. 166 nodes because there are 166 total unique users, comments, and targets in the toy dataset. 
# 350 edges because each comment can target multiple players, and there are 350 total interactions in the toy dataset.
#
# 3. Not every target is a player. Look at `entity_type` -- in `toy` they all
#    happen to be players, but in `small` there are teams too. Set `kind` from
#    `entity_type` rather than hard-coding "player".
#  
def build(d):
    G4 = nx.DiGraph()
    for row in d["interactions"].itertuples(index=False):
        G4.add_node(row.author_id, kind="user", label=row.author_username)
        G4.add_node(row.comment_id, kind="comment")
        G4.add_node(row.target_id, kind=row.entity_type, label=row.entity_text)
        G4.add_edge(row.author_id, row.comment_id, kind="authored")
        G4.add_edge(row.comment_id, row.target_id, kind="targets", is_abusive=row.is_abusive)
    return G4
#
# 4. In `small` and beyond, some rows have an EMPTY `target_id`: the annotator
#    could not work out who was meant. Decide what to do with those rows and
#    write down why. There is no right answer, only a documented one.
#
# if there is no target_id, i would just skip that row and not add it to the graph because it's
# not relevant to what we're looking for.
#
# 5. When it works, open `plot_graph.py`.
#
# Check yourself: `reference/toy_graph_reference.png` is what the finished
# `toy` graph looks like. Yours will not be laid out identically -- the layout
# is random -- but it should have the same shape and the same counts.
