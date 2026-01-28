import pandas as pd
import numpy as np
import re
import networkx as nx


# ======================================================
# DATA LOADING & BASIC VALIDATION
# ======================================================

def load_data(file_path):
    """
    Loads UK Top 50 dataset and performs basic validation
    """

    df = pd.read_csv(file_path)

    # Remove duplicates and missing critical values
    df = df.drop_duplicates()
    df = df.dropna(subset=["date", "position", "song", "artist"])

    # Correct data types
    df["position"] = df["position"].astype(int)
    df["date"] = pd.to_datetime(df["date"])

    return df


# ======================================================
# ARTIST NAME STANDARDIZATION
# ======================================================

def normalize_artist_names(df):
    """
    Standardizes artist names and prepares collaboration lists
    """

    def clean_artist_name(name):
        name = name.lower()
        name = re.sub(r"feat\.|ft\.|and", "&", name)
        name = name.replace(" ", "")
        return name

    df["artist_clean"] = df["artist"].apply(clean_artist_name)
    df["artist_list"] = df["artist_clean"].str.split("&")

    return df


# ======================================================
# EXPLODE ARTIST DATA (FOR DOMINANCE METRICS)
# ======================================================

def create_artist_level_table(df):
    """
    Converts multi-artist tracks into artist-level rows
    """
    return df.explode("artist_list")


# ======================================================
# KPI CALCULATIONS
# ======================================================

def calculate_market_kpis(track_df, artist_df):
    """
    Computes all major market structure KPIs
    """

    total_tracks = len(track_df)

    # Artist dominance
    artist_frequency = artist_df["artist_list"].value_counts()
    artist_share = artist_frequency / total_tracks

    artist_concentration_index = (artist_share ** 2).sum()
    top5_artist_share = artist_share.head(5).sum()

    # Diversity metrics
    unique_artist_count = artist_df["artist_list"].nunique()
    diversity_score = unique_artist_count / total_tracks

    # Collaboration metrics
    track_df["is_collaboration"] = track_df["artist"].str.contains("&")
    collaboration_ratio = track_df["is_collaboration"].mean()

    # Explicit content metrics
    explicit_content_share = track_df["is_explicit"].mean()

    # Album format distribution
    album_distribution = track_df["album_type"].value_counts(normalize=True)

    # Content variety
    content_variety_index = track_df["song"].nunique() / total_tracks

    kpis = {
        "ACI": artist_concentration_index,
        "Top5Share": top5_artist_share,
        "UniqueArtists": unique_artist_count,
        "DiversityScore": diversity_score,
        "CollaborationRatio": collaboration_ratio,
        "ExplicitShare": explicit_content_share,
        "AlbumDistribution": album_distribution,
        "ContentVariety": content_variety_index
    }

    return kpis, artist_frequency


# ======================================================
# TRACK DURATION ANALYSIS
# ======================================================

def add_duration_features(df):
    """
    Converts duration into minutes and buckets
    """

    df["duration_minutes"] = df["duration_ms"] / 60000

    df["duration_bucket"] = pd.cut(
        df["duration_minutes"],
        bins=[0, 2, 3, 4, 10],
        labels=["Short", "Medium", "Long", "Very Long"]
    )

    return df


# ======================================================
# RANK SEGMENTATION
# ======================================================

def create_rank_groups(df):
    """
    Groups tracks by ranking segments
    """

    def rank_category(rank):
        return "Top 10" if rank <= 10 else "Top 50"

    df["rank_group"] = df["position"].apply(rank_category)

    return df


# ======================================================
# COLLABORATION NETWORK CREATION
# ======================================================

def build_artist_collaboration_network(df):
    """
    Builds network graph of artist collaborations
    """

    graph = nx.Graph()

    for artists in df["artist_list"]:
        if isinstance(artists, list) and len(artists) > 1:
            for i in range(len(artists)):
                for j in range(i + 1, len(artists)):
                    graph.add_edge(artists[i], artists[j])

    return graph
