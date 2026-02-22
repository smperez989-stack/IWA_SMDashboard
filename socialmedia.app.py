import streamlit as st
import pandas as pd
import plotly.express as px

# =========================================
# 1. Page config
# =========================================
st.set_page_config(
    page_title="IWA Social Media Dashboard",
    layout="wide"
)

st.title("IWA Social Media Analytics")

st.write(
    "Dashboard by social network (Facebook, Instagram, LinkedIn) "
    "showing monthly trends for followers, views, posts, interactions, and comments."
)

# =========================================
# 2. Load data
# =========================================
@st.cache_data
def load_data(file_obj):
    xls = pd.ExcelFile(file_obj)

    data = {}
    sheet_map = {
        "Facebook": "FB Page",
        "Instagram": "Instagram",
        "LinkedIn": "LinkedIn"
    }

    for label, sheet_name in sheet_map.items():
        df = pd.read_excel(xls, sheet_name)

        # Create a Date column from Year + Month
        df["Date"] = pd.to_datetime(
            df["Year"].astype(str) + "-" + df["Month"].astype(str),
            format="%Y-%B"
        )

        df = df.sort_values("Date")
        data[label] = df

    return data


# =========================================
# 3. File input
# =========================================
st.sidebar.header("Data source")

uploaded_file = st.sidebar.file_uploader(
    "Upload IWA SM Analytics Excel file",
    type=["xlsx"]
)

if uploaded_file is not None:
    data_dict = load_data(uploaded_file)
else:
    # If you run this locally, put the Excel in the same folder as app.py
    default_path = "IWA SM Analytics.xlsx"
    try:
        data_dict = load_data(default_path)
        st.sidebar.success(f"Using local file: {default_path}")
    except Exception as e:
        st.sidebar.error("No file uploaded and default file not found.")
        st.stop()


# =========================================
# 4. Helper to generate textual key insights
#    (Updated: November vs December + works without a "Date" column)
# =========================================
import pandas as pd

def _add_sort_date_if_missing(df: pd.DataFrame) -> pd.DataFrame:
    """
    Creates a sortable 'Date' column using Year + Month if 'Date' is missing.
    Assumes Month is a month name in English (e.g., 'December', 'January').
    """
    df = df.copy()

    if "Date" not in df.columns:
        month_order = [
            "January","February","March","April","May","June",
            "July","August","September","October","November","December"
        ]
        month_map = {m: i for i, m in enumerate(month_order, start=1)}

        # Safe conversion (handles unexpected month values)
        df["_month_num"] = df["Month"].map(month_map)

        # Build a first-day-of-month date for sorting
        df["Date"] = pd.to_datetime(
            dict(year=df["Year"], month=df["_month_num"], day=1),
            errors="coerce"
        )

        df.drop(columns=["_month_num"], inplace=True)

    return df


def generate_insight_text(df: pd.DataFrame, network_name: str,
                          month_a: str = "December", month_b: str = "January") -> str:
    df = _add_sort_date_if_missing(df)

    # Keep only the two months we want to compare
    df_subset = df[df["Month"].isin([month_a, month_b])].copy()

    if df_subset["Month"].nunique() < 2:
        return (
            f"For {network_name}, we still need data for both {month_a} and {month_b} "
            "to compare one month against the other."
        )

    metrics = ["Followers", "Views", "Posts", "Interactions", "Comments"]

    changes_a_b = {"up": [], "down": [], "stable": []}

    for metric in metrics:
        if metric in df_subset.columns:
            a_val = df_subset[df_subset["Month"] == month_a][metric].sum()
            b_val = df_subset[df_subset["Month"] == month_b][metric].sum()

            if b_val > a_val:
                changes_a_b["up"].append(metric.lower())
            elif b_val < a_val:
                changes_a_b["down"].append(metric.lower())
            else:
                changes_a_b["stable"].append(metric.lower())

    # Overall trend: compare first vs last available month (by Date)
    df_sorted = df.sort_values("Date").dropna(subset=["Date"])
    first_month = df_sorted["Month"].iloc[0]
    last_month = df_sorted["Month"].iloc[-1]

    trends_all = {"up": [], "down": [], "mixed": []}

    for metric in metrics:
        if metric in df_sorted.columns:
            first_val = df_sorted[metric].iloc[0]
            last_val = df_sorted[metric].iloc[-1]

            if last_val > first_val:
                trends_all["up"].append(metric.lower())
            elif last_val < first_val:
                trends_all["down"].append(metric.lower())
            else:
                trends_all["mixed"].append(metric.lower())

    # Simple text for month_a vs month_b
    parts_a_b = []
    if changes_a_b["up"]:
        parts_a_b.append(f"{', '.join(changes_a_b['up'])} went up from {month_a} to {month_b}")
    if changes_a_b["down"]:
        parts_a_b.append(f"{', '.join(changes_a_b['down'])} went down from {month_a} to {month_b}")
    if changes_a_b["stable"]:
        parts_a_b.append(f"{', '.join(changes_a_b['stable'])} stayed at a similar level")

    sentence_a_b = "; ".join(parts_a_b) + "." if parts_a_b else (
        f"There are only small changes between {month_a} and {month_b}."
    )

    # Simple text across all months
    parts_all = []
    if trends_all["up"]:
        parts_all.append(f"over all months, {', '.join(trends_all['up'])} show a general increase")
    if trends_all["down"]:
        parts_all.append(
            f"{', '.join(trends_all['down'])} move slightly down when we compare {first_month} and {last_month}"
        )
    if trends_all["mixed"]:
        parts_all.append(
            f"{', '.join(trends_all['mixed'])} move in a more irregular way, with some stronger and weaker months"
        )

    sentence_all = "; ".join(parts_all) + "." if parts_all else (
        "Across all months, the metrics move in different ways without one clear pattern."
    )

    return (
        f"For {network_name}, when we compare {month_a} and {month_b}, "
        f"{sentence_a_b} "
        f"Looking at all months, {sentence_all}"
    )


def show_key_insights(df: pd.DataFrame, network_name: str):
    st.markdown("**📌 Key insights**")
    insight_text = generate_insight_text(df, network_name, month_a="December", month_b="January")
    st.markdown(insight_text)

# =========================================
# 5. Helper to plot one social network
# =========================================
def show_network_section(network_name, df, color_sequence=None):
    st.subheader(network_name)

    metrics = ["Followers", "Views", "Posts", "Interactions", "Comments"]

    selected_metrics = st.multiselect(
        f"Select metrics to display for {network_name}:",
        metrics,
        default=["Views", "Followers"],
        key=f"{network_name}_metrics"
    )

    if not selected_metrics:
        st.info("Please select at least one metric.")
        return

    plot_df = df[["Date"] + selected_metrics]

    fig = px.line(
        plot_df,
        x="Date",
        y=selected_metrics,
        markers=True,
        color_discrete_sequence=(
            color_sequence
            if color_sequence is not None
            and len(color_sequence) >= len(selected_metrics)
            else None
        )
    )

    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Value",
        legend_title="Metric",
        hovermode="x unified"
    )

    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Show data table"):
        st.dataframe(df)

    show_key_insights(df, network_name)


# =========================================
# 6. Color palettes por red social
# =========================================
facebook_colors = [
    "#4267B2", "#89CFF0", "#003f5c", "#2f4b7c", "#665191"
]

instagram_colors = [
    "#ff9a9e", "#ff99aa", "#ff7e5f", "#fcb045", "#fdc830"
]

linkedin_colors = [
    "#0077b5", "#00b894", "#0984e3", "#55efc4", "#74b9ff"
]


# =========================================
# 7. Single-page layout (all sections)
# =========================================

# ---- Resumen general ----
st.header("📊 Overall Summary")

st.markdown("""
Here is a simple overview of how each social network is doing:

**Facebook**  
Facebook stays quite stable from month to month. It keeps a steady audience and regular activity. It works well to maintain general visibility.

**Instagram**  
Instagram is the most dynamic platform. When we post more content, activity grows fast. It is our strongest channel to reach new people and create visual impact.

**LinkedIn**  
LinkedIn grows slowly but in a steady way. It is useful to connect with professionals, share our achievements, and support our community work. Even if the numbers are smaller, the interactions are more focused.

**Overall**  
Instagram has the highest movement and reach.  
Facebook is stable and reliable.  
LinkedIn supports our professional image.

Each platform adds a different and important value for IWA.
""")

st.markdown("---")

# ---- Facebook ----
st.header("📘 Facebook")
show_network_section("Facebook", data_dict["Facebook"], color_sequence=facebook_colors)

st.markdown("---")

# ---- Instagram ----
st.header("📷 Instagram")
show_network_section("Instagram", data_dict["Instagram"], color_sequence=instagram_colors)

st.markdown("---")

# ---- LinkedIn ----
st.header("💼 LinkedIn")
show_network_section("LinkedIn", data_dict["LinkedIn"], color_sequence=linkedin_colors)
