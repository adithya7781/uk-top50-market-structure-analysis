import pandas as pd
import numpy as np
import re
import networkx as nx

# ----------------------
# Load + Clean Data
# ----------------------

def load_data(path):
    df = pd.read_csv(path)

    # Basic validation
    df = df.drop_duplicates()
    df = df.dropna(subset=["date", "position", "song", "artist"])

    df["position"] = df["position"].astype(int)
    df["date"] = pd.to_datetime(df["date"])

    return df


# ----------------------
# Artist Normalization
# ----------------------

def normalize_artists(df):

    def clean_artist(name):
        name = name.lower()
        name = re.sub(r"feat\.|ft\.|and", "&", name)
        name = name.replace(" ", "")
        return name

    df["artist_clean"] = df["artist"].apply(clean_artist)
    df["artist_list"] = df["artist_clean"].str.split("&")

    return df


# ----------------------
# Explode Artist Table
# ----------------------

def explode_artists(df):
    return df.explode("artist_list")


# ----------------------
# KPI Calculations
# ----------------------

def calculate_kpis(df, artist_df):

    total_entries = len(df)

    # Artist dominance
    artist_counts = artist_df["artist_list"].value_counts()
    artist_shares = artist_counts / total_entries

    artist_concentration_index = (artist_shares ** 2).sum()
    top5_concentration = artist_shares.head(5).sum()

    # Diversity
    unique_artist_count = artist_df["artist_list"].nunique()
    diversity_score = unique_artist_count / total_entries

    # Collaboration ratio
    df["is_collab"] = df["artist"].str.contains("&")
    collaboration_ratio = df["is_collab"].mean()

    # Explicit share
    explicit_share = df["is_explicit"].mean()

    # Single vs Album ratio
    album_ratio = df["album_type"].value_counts(normalize=True)

    # Content variety index (unique songs / total)
    content_variety_index = df["song"].nunique() / total_entries

    kpis = {
        "ACI": artist_concentration_index,
        "Top5": top5_concentration,
        "UniqueArtists": unique_artist_count,
        "Diversity": diversity_score,
        "CollaborationRatio": collaboration_ratio,
        "ExplicitShare": explicit_share,
        "AlbumRatio": album_ratio,
        "ContentVariety": content_variety_index
    }

    return kpis, artist_counts


# ----------------------
# Duration Buckets
# ----------------------

def duration_analysis(df):

    df["duration_min"] = df["duration_ms"] / 60000

    df["duration_bucket"] = pd.cut(
        df["duration_min"],
        bins=[0,2,3,4,10],
        labels=["Short","Medium","Long","Very Long"]
    )

    return df


# ----------------------
# Rank Buckets
# ----------------------

def rank_groups(df):

    def bucket(rank):
        if rank <= 10:
            return "Top 10"
        else:
            return "Top 50"

    df["rank_group"] = df["position"].apply(bucket)

    return df


# ----------------------
# Collaboration Network
# ----------------------

def build_collaboration_network(df):

    G = nx.Graph()

    for artists in df["artist_list"]:
        if isinstance(artists, list) and len(artists) > 1:
            for i in range(len(artists)):
                for j in range(i + 1, len(artists)):
                    G.add_edge(artists[i], artists[j])

    return G
