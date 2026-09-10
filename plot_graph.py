"""EXAMPLE: drawing the graph from build_graph.py.

Same three hand-typed rows, so you can see exactly which line of code produces
which mark on the page. Also DELIBERATELY UNFINISHED.

    python plot_graph.py          # writes my_graph.png

Compare what you eventually produce with reference/toy_graph_reference.png.
"""
import matplotlib
matplotlib.use("Agg")          # draw to a file, not to a window
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import networkx as nx

from load_data import load


# --- one colour and one shape per kind of node -----------------------------
# Keep these consistent everywhere. A reader should learn the key once.
STYLE = {
    "user":    {"colour": "#2f6fdb", "shape": "o", "size": 700},
    "comment": {"colour": "#c9ccd1", "shape": "s", "size": 120},
    "player":  {"colour": "#e08b2a", "shape": "^", "size": 600},
    "team":    {"colour": "#2e9e6b", "shape": "D", "size": 600},
}
ABUSIVE_COLOUR = "#cc2b2b"     # red: is_abusive == "YES"
PLAIN_COLOUR = "#c3c8cf"       # grey: everything else


def build_tiny_graph():
    """The same three rows build_graph.py uses, so the two files line up."""
    d = load("toy")
    G = nx.DiGraph()
    for row in d["interactions"].head(3).itertuples(index=False):
        G.add_node(row.author_id, kind="user", label=row.author_username)
        G.add_node(row.comment_id, kind="comment", label=row.comment_id)
        G.add_node(row.target_id, kind="player", label=row.entity_text)
        G.add_edge(row.author_id, row.comment_id, kind="authored")
        G.add_edge(row.comment_id, row.target_id,
                   kind="targets", is_abusive=row.is_abusive)
    return G


def draw(G, path="my_graph.png", title="my graph"):
    # 1. WHERE do the nodes go? A layout is an algorithm that assigns an (x, y)
    #    to every node. `spring_layout` pretends edges are springs and lets the
    #    whole thing settle. `seed` fixes the randomness so you get the same
    #    picture twice.
    pos = nx.spring_layout(G.to_undirected(), seed=7)

    fig, ax = plt.subplots(figsize=(9, 7))

    # 2. EDGES first, so nodes are drawn on top of them.
    #    Split them into two lists: abusive and everything else.
    abusive = [(a, b) for a, b, e in G.edges(data=True)
               if e.get("is_abusive") == "YES"]
    plain = [(a, b) for a, b, e in G.edges(data=True)
             if e.get("is_abusive") != "YES"]

    nx.draw_networkx_edges(G, pos, ax=ax, edgelist=plain,
                           edge_color=PLAIN_COLOUR, width=1.2, arrows=False)
    nx.draw_networkx_edges(G, pos, ax=ax, edgelist=abusive,
                           edge_color=ABUSIVE_COLOUR, width=2.5, arrows=False)

    # 3. NODES, one call per kind, so each kind gets its own colour and shape.
    for kind, style in STYLE.items():
        nodes = [n for n, k in G.nodes(data="kind") if k == kind]
        if not nodes:
            continue
        nx.draw_networkx_nodes(G, pos, ax=ax, nodelist=nodes,
                               node_color=style["colour"],
                               node_shape=style["shape"],
                               node_size=style["size"],
                               edgecolors="#33373d", linewidths=0.8)

    # 4. LABELS. Readable at this size; at 200 nodes they turn into a smear and
    #    you will want to label only the interesting ones.
    labels = {n: a for n, a in G.nodes(data="label")}
    nx.draw_networkx_labels(G, pos, ax=ax, labels=labels, font_size=8)

    # 5. A LEGEND. A figure nobody can decode is not a figure.
    handles = [Line2D([], [], color="w", marker=s["shape"], markersize=11,
                      markerfacecolor=s["colour"], markeredgecolor="#33373d",
                      label=k)
               for k, s in STYLE.items()
               if any(kk == k for _, kk in G.nodes(data="kind"))]
    handles += [Line2D([], [], color=ABUSIVE_COLOUR, lw=2.5,
                       label="targets edge, is_abusive=YES"),
                Line2D([], [], color=PLAIN_COLOUR, lw=1.5, label="other edge")]
    ax.legend(handles=handles, loc="upper left", fontsize=9)

    ax.set_title(title)
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(path, dpi=150, facecolor="white")
    plt.close(fig)
    print("wrote", path)


if __name__ == "__main__":
    G = build_tiny_graph()
    print(G.number_of_nodes(), "nodes,", G.number_of_edges(), "edges")
    draw(G, "my_graph.png", "three rows of the toy dataset")


# ===========================================================================
# TODO -- your turn
# ===========================================================================
#
# 1. Import your finished `build` from build_graph.py and draw the whole `toy`
#    dataset instead of three rows. It will look messy. That is expected.
#
# 2. The comment nodes are the problem: there are 130 of them and only 15
#    users. Try making them much smaller, and much paler. Better?
#
# 3. Turn the labels off for comments (keep them for users and players). Look
#    at `reference/toy_graph_reference.png` -- which labels did it keep?
#
# 4. Try `nx.spring_layout(..., k=0.3)` and `k=2.0` and see what `k` does.
#    Then try `nx.kamada_kawai_layout`. Which is easier to read, and why?
#
# 5. Save a version with only the abusive edges drawn. What can you see that
#    you could not see before? What did you lose?
#
# 6. Open interactive/toy.html and do the seven-step tour. Several of the
#    things you just built by hand are switches in there. Which of your five
#    plots above does step 2 of the tour replace?
