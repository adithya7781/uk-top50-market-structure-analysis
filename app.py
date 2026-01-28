import streamlit as st
import pandas as pd
import plotly.express as px
from analysis import *
from pyvis.network import Network
import streamlit.components.v1 as components

# ----------------------
# Page Config
# ----------------------

st.set_page_config(page_title="UK Top 50 Market Analysis", layout="wide")

st.title("United Kingdom Top 50 Playlist Market Structure Analysis")

# ----------------------
# Load Data (Cached)
# ----------------------

@st.cache_data
def load_pipeline():
    df = load_data("data/Atlantic_United_Kingdom.csv")
    df = normalize_artists(df)
    artist_df = explode_artists(df)
    df = duration_analysis(df)
    df = rank_groups(df)
    return df, artist_df


df, artist_df = load_pipeline()

# ----------------------
# Sidebar Filters
# ----------------------

st.sidebar.header("Filters")

date_range = st.sidebar.date_input(
    "Date Range",
    [df.date.min(), df.date.max()]
)

album_filter = st.sidebar.multiselect(
    "Album Type",
    df.album_type.unique(),
    default=df.album_type.unique()
)

artist_filter = st.sidebar.multiselect(
    "Select Artist",
    sorted(df.artist.unique())
)

collab_toggle = st.sidebar.selectbox(
    "Track Type",
    ["All", "Solo Only", "Collaborations Only"]
)

# ----------------------
# Apply Filters
# ----------------------

filtered = df[
    (df["date"] >= pd.to_datetime(date_range[0])) &
    (df["date"] <= pd.to_datetime(date_range[1])) &
    (df["album_type"].isin(album_filter))
]

if artist_filter:
    filtered = filtered[filtered["artist"].isin(artist_filter)]

if collab_toggle == "Solo Only":
    filtered = filtered[~filtered["artist"].str.contains("&")]

elif collab_toggle == "Collaborations Only":
    filtered = filtered[filtered["artist"].str.contains("&")]

filtered_artist_df = explode_artists(filtered)

# ----------------------
# KPI Section
# ----------------------

kpis, artist_counts = calculate_kpis(filtered, filtered_artist_df)

col1, col2, col3, col4, col5, col6 = st.columns(6)

col1.metric("Artist Concentration Index", round(kpis["ACI"],3))
col2.metric("Top 5 Artist Share", f"{round(kpis['Top5']*100,1)}%")
col3.metric("Unique Artists", kpis["UniqueArtists"])
col4.metric("Collaboration Ratio", f"{round(kpis['CollaborationRatio']*100,1)}%")
col5.metric("Explicit Content Share", f"{round(kpis['ExplicitShare']*100,1)}%")
col6.metric("Content Variety Index", round(kpis["ContentVariety"],2))

# ----------------------
# Artist Dominance Leaderboard
# ----------------------

st.subheader("Artist Dominance Leaderboard")

top_artists = artist_counts.head(15)

fig1 = px.bar(
    top_artists,
    orientation="h",
    title="Top 15 Artists by Playlist Presence"
)

st.plotly_chart(fig1, width="stretch")

# ----------------------
# Explicit Content Analysis
# ----------------------

st.subheader("Explicit vs Clean Content")

fig2 = px.pie(
    filtered,
    names="is_explicit",
    title="Explicit Content Share"
)

st.plotly_chart(fig2, width="stretch")

# Rank Distribution

fig3 = px.box(
    filtered,
    x="is_explicit",
    y="position",
    title="Rank Distribution: Explicit vs Clean"
)

st.plotly_chart(fig3, width="stretch")

# ----------------------
# Album Strategy Analysis
# ----------------------

st.subheader("Single vs Album Distribution")

fig4 = px.bar(
    filtered["album_type"].value_counts(),
    title="Release Format Dominance"
)

st.plotly_chart(fig4, width="stretch")

# Album size vs presence

fig5 = px.scatter(
    filtered,
    x="total_tracks",
    y="position",
    title="Album Size vs Chart Position"
)

st.plotly_chart(fig5, width="stretch")

# ----------------------
# Track Duration Insights
# ----------------------

st.subheader("Track Duration Analysis")

fig6 = px.histogram(
    filtered,
    x="duration_bucket",
    title="Track Duration Distribution"
)

st.plotly_chart(fig6, width="stretch")

fig7 = px.scatter(
    filtered,
    x="duration_min",
    y="popularity",
    title="Duration vs Popularity"
)

st.plotly_chart(fig7, width="stretch")

# ----------------------
# Collaboration Network
# ----------------------

st.subheader("Artist Collaboration Network")

G = build_collaboration_network(filtered)

if len(G.nodes) > 0:

    net = Network(height="500px", bgcolor="white")
    net.from_nx(G)
    net.save_graph("network.html")

    HtmlFile = open("network.html", "r", encoding="utf-8")
    components.html(HtmlFile.read(), height=550)

else:
    st.info("No collaborations found for selected filters.")
