import streamlit as st
import pandas as pd
import plotly.express as px
from pyvis.network import Network
import streamlit.components.v1 as components

from analysis import *

st.markdown("""
<style>
div[data-testid="metric-container"] {
    background-color: #161B22;
    border: 1px solid #30363D;
    padding: 18px;
    border-radius: 12px;
    text-align: center;
    box-shadow: 0px 0px 8px rgba(0,0,0,0.3);
}

div[data-testid="metric-container"] > label {
    font-size: 14px;
    color: #C9D1D9;
}

div[data-testid="metric-container"] > div {
    font-size: 26px;
    font-weight: bold;
    color: #58A6FF;
}
</style>
""", unsafe_allow_html=True)


# ======================================================
# PAGE CONFIGURATION
# ======================================================

st.set_page_config(
    page_title="UK Top 50 Market Structure Analysis",
    layout="wide"
)

st.title("United Kingdom Top 50 Playlist Market Structure Dashboard")


# ======================================================
# DATA PIPELINE (CACHED FOR PERFORMANCE)
# ======================================================

@st.cache_data
def load_full_pipeline():

    df = load_data("data/Atlantic_United_Kingdom.csv")
    df = normalize_artist_names(df)

    artist_level_df = create_artist_level_table(df)

    df = add_duration_features(df)
    df = create_rank_groups(df)

    return df, artist_level_df


with st.spinner("Loading UK Market Structure Analysis....."):
    track_data, artist_data = load_full_pipeline()


# ======================================================
# SIDEBAR FILTERS
# ======================================================

st.sidebar.header("Dashboard Filters")

date_range = st.sidebar.date_input(
    "Select Date Range",
    [track_data.date.min(), track_data.date.max()]
)

album_filter = st.sidebar.multiselect(
    "Album Type",
    track_data.album_type.unique(),
    default=track_data.album_type.unique()
)

artist_filter = st.sidebar.multiselect(
    "Artist Filter",
    sorted(track_data.artist.unique())
)

track_type_filter = st.sidebar.selectbox(
    "Track Type",
    ["All", "Solo Only", "Collaborations Only"]
)


# ======================================================
# APPLY FILTERS
# ======================================================

filtered_data = track_data[
    (track_data["date"] >= pd.to_datetime(date_range[0])) &
    (track_data["date"] <= pd.to_datetime(date_range[1])) &
    (track_data["album_type"].isin(album_filter))
]

if artist_filter:
    filtered_data = filtered_data[filtered_data["artist"].isin(artist_filter)]

if track_type_filter == "Solo Only":
    filtered_data = filtered_data[~filtered_data["artist"].str.contains("&")]

elif track_type_filter == "Collaborations Only":
    filtered_data = filtered_data[filtered_data["artist"].str.contains("&")]

filtered_artist_data = create_artist_level_table(filtered_data)


# ======================================================
# KPI COMPUTATION
# ======================================================

kpis, artist_frequency = calculate_market_kpis(filtered_data, filtered_artist_data)


# ======================================================
# KPI DISPLAY SECTION
# ======================================================

kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)

kpi1.metric("Artist Concentration Index", round(kpis["ACI"], 3))
kpi2.metric("Top 5 Artist Share", f"{round(kpis['Top5Share'] * 100, 1)}%")
kpi3.metric("Unique Artists", kpis["UniqueArtists"])
kpi4.metric("Collaboration Ratio", f"{round(kpis['CollaborationRatio'] * 100, 1)}%")
kpi5.metric("Explicit Content Share", f"{round(kpis['ExplicitShare'] * 100, 1)}%")
kpi6.metric("Content Variety Index", round(kpis["ContentVariety"], 2))


# ======================================================
# ARTIST DOMINANCE LEADERBOARD
# ======================================================

st.subheader("Artist Dominance Leaderboard")

top_artists = artist_frequency.head(15)

artist_chart = px.bar(
    top_artists,
    orientation="h",
    title="Top Artists by Playlist Presence"
)

st.plotly_chart(artist_chart, width="stretch")

st.markdown("""
### Market Insight
- A higher concentration among top artists indicates strong superstar dominance in the UK market.
- Labels can prioritize premium artist signings and focused promotional investments.
""")


# ======================================================
# EXPLICIT CONTENT ANALYSIS
# ======================================================

st.subheader("Explicit Content Performance")

explicit_pie = px.pie(
    filtered_data,
    names="is_explicit",
    title="Explicit vs Clean Content Share"
)

st.plotly_chart(explicit_pie, width="stretch")


explicit_rank_box = px.box(
    filtered_data,
    x="is_explicit",
    y="position",
    title="Chart Rank Distribution by Content Type"
)

st.plotly_chart(explicit_rank_box, width="stretch")

st.markdown("""
### Content Localization Insight
- Clean tracks consistently perform better in higher chart positions.
- This indicates UK listener sensitivity toward radio-friendly and mainstream content.
""")


# ======================================================
# ALBUM STRATEGY ANALYSIS
# ======================================================

st.subheader("Release Format Strategy")

album_chart = px.bar(
    filtered_data["album_type"].value_counts(),
    title="Single vs Album Presence"
)

st.plotly_chart(album_chart, width="stretch")


album_size_scatter = px.scatter(
    filtered_data,
    x="total_tracks",
    y="position",
    title="Album Size vs Chart Position"
)

st.plotly_chart(album_size_scatter, width="stretch")

st.markdown("""
### Release Strategy Insight
- Singles dominate playlist presence compared to album tracks.
- UK market favors frequent single releases over full-album launch strategies.
""")


# ======================================================
# TRACK DURATION INSIGHTS
# ======================================================

st.subheader("Track Duration Patterns")

duration_hist = px.histogram(
    filtered_data,
    x="duration_bucket",
    title="Track Duration Distribution"
)

st.plotly_chart(duration_hist, width="stretch")


duration_popularity = px.scatter(
    filtered_data,
    x="duration_minutes",
    y="popularity",
    title="Track Duration vs Popularity"
)

st.plotly_chart(duration_popularity, width="stretch")

st.markdown("""
### Listener Preference Insight
- Medium-duration tracks show higher engagement and popularity.
- Extremely long tracks tend to perform weaker on curated playlists.
""")


# ======================================================
# COLLABORATION NETWORK VISUALIZATION
# ======================================================

st.subheader("Artist Collaboration Network")

network_graph = build_artist_collaboration_network(filtered_data)

if len(network_graph.nodes) > 0:

    network = Network(height="500px", bgcolor="#0E1117", font_color="white")
    network.from_nx(network_graph)
    network.save_graph("network.html")

    html_file = open("network.html", "r", encoding="utf-8")
    components.html(html_file.read(), height=550)

else:
    st.info("No collaborations available for selected filters.")
