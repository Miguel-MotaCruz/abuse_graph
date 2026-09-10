"""Load a dataset into pandas DataFrames.

This file is finished — you do not need to change it. Read it, though: it is
about 60 lines and it is the only thing standing between you and the data.

    from load_data import load
    d = load("toy")
    d["comments"].head()
"""
import os
import pandas as pd

# Every dataset has these files. See SCHEMA.md for what the columns mean.
TABLES = ["teams", "players", "games", "submissions",
          "comments", "comment_entities", "comment_labels_weak", "users"]

HERE = os.path.dirname(os.path.abspath(__file__))


def load(dataset="toy", root=None):
    """Read one dataset. Returns a dict of DataFrames.

    dataset: "toy", "small", "medium", "large" or "annotated_sample"
    """
    folder = os.path.join(root or os.path.join(HERE, "data"), dataset)
    if not os.path.isdir(folder):
        raise FileNotFoundError(
            f"No dataset at {folder}. Only 'toy' and 'small' ship with this "
            f"repository; ask your supervisor for the others.")

    d = {}
    for name in TABLES:
        path = os.path.join(folder, name + ".csv")
        if os.path.exists(path):
            d[name] = pd.read_csv(path, dtype={"target_id": "string",
                                               "game_id": "string"})

    # Timestamps arrive as text like "2025-11-08 22:14:03 UTC". Turn them into
    # real datetimes so you can sort and subtract them.
    for table, column in [("comments", "comment_timestamp"),
                          ("submissions", "submission_timestamp")]:
        if table in d and column in d[table]:
            d[table][column] = pd.to_datetime(
                d[table][column], format="%Y-%m-%d %H:%M:%S UTC",
                utc=True, errors="coerce")

    if "games" in d:
        g = d["games"]
        g["date_utc"] = pd.to_datetime(g["date_utc"], utc=True, format="mixed")
        # who won, who lost, and by how much -- you will want these later
        home_won = g["home_score"] > g["away_score"]
        g["winner_team_id"] = g["team_home_id"].where(home_won, g["team_away_id"])
        g["loser_team_id"] = g["team_away_id"].where(home_won, g["team_home_id"])
        g["margin"] = (g["home_score"] - g["away_score"]).abs()

    d["interactions"] = build_interactions(d)
    return d


def build_interactions(d):
    """One row per (comment, target). THIS is the table you will use most.

    Not one row per comment: a comment naming three people appears three times,
    once per target, and the three rows can have different `is_abusive` values.
    That is the single most important thing about this data.
    """
    x = d["comment_entities"].merge(
        d["comments"][["comment_id", "submission_id", "author_id",
                       "author_username", "comment_timestamp", "parent_id"]],
        on="comment_id", how="left")

    x = x.merge(
        d["submissions"][["submission_id", "game_id", "submission_kind",
                          "submission_timestamp"]],
        on="submission_id", how="left")

    # A convenient boolean. `is_abusive` is the text "YES" or "NO".
    x["is_abusive_yes"] = x["is_abusive"].eq("YES")
    return x


def describe(d):
    """Print how big everything is. Run this first, every time."""
    for name, table in d.items():
        print(f"{name:22s} {len(table):>7,} rows   {len(table.columns):>2} columns")


if __name__ == "__main__":
    data = load("toy")
    describe(data)
    print()
    print("first three interactions:")
    print(data["interactions"][["comment_id", "author_username", "entity_text",
                                "entity_type", "is_abusive"]].head(3).to_string(index=False))
