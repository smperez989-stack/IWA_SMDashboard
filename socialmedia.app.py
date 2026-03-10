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
#    (Automatic comparison of the last two months in the file)
# =========================================
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

        df["_month_num"] = df["Month"].map(month_map)

        df["Date"] = pd.to_datetime(
            dict(year=df["Year"], month=df["_month_num"], day=1),
            errors="coerce"
        )

        df.drop(columns=["_month_num"], inplace=True)

    return df


def generate_insight_text(df: pd.DataFrame, network_name: str) -> str:
    df = _add_sort_date_if_missing(df)

    metrics = ["Followers", "Views", "Posts", "Interactions", "Comments"]

    # Keep valid dates only and sort
    df_sorted = df.dropna(subset=["Date"]).sort_values("Date").copy()

    if df_sorted.empty or len(df_sorted["Date"].unique()) < 2:
        return (
            f"For {network_name}, there is not enough monthly data yet to compare "
            "the last two months available in the file."
        )

    # Get the last two available months automatically
    last_two_dates = sorted(df_sorted["Date"].unique())[-2:]
    prev_date = pd.Timestamp(last_two_dates[0])
    last_date = pd.Timestamp(last_two_dates[1])

    prev_row = df_sorted[df_sorted["Date"] == prev_date].iloc[-1]
    last_row = df_sorted[df_sorted["Date"] == last_date].iloc[-1]

    prev_label = prev_date.strftime("%B %Y")
    last_label = last_date.strftime("%B %Y")

    changes_last_two = {"up": [], "down": [], "stable": []}

    for metric in metrics:
        if metric in df_sorted.columns:
            prev_val = prev_row[metric]
            last_val = last_row[metric]

            if pd.notna(prev_val) and pd.notna(last_val):
                if last_val > prev_val:
                    changes_last_two["up"].append(metric.lower())
                elif last_val < prev_val:
                    changes_last_two["down"].append(metric.lower())
                else:
                    changes_last_two["stable"].append(metric.lower())

    # Overall trend: compare first vs last available month
    first_row = df_sorted.iloc[0]
    last_row_all = df_sorted.iloc[-1]

    first_label = pd.to_datetime(first_row["Date"]).strftime("%B %Y")
    final_label = pd.to_datetime(last_row_all["Date"]).strftime("%B %Y")

    trends_all = {"up": [], "down": [], "mixed": []}

    for metric in metrics:
        if metric in df_sorted.columns:
            first_val = first_row[metric]
            final_val = last_row_all[metric]

            if pd.notna(first_val) and pd.notna(final_val):
                if final_val > first_val:
                    trends_all["up"].append(metric.lower())
                elif final_val < first_val:
                    trends_all["down"].append(metric.lower())
                else:
                    trends_all["mixed"].append(metric.lower())

    # Text for automatic last-two-month comparison
    parts_last_two = []
    if changes_last_two["up"]:
        parts_last_two.append(
            f"{', '.join(changes_last_two['up'])} went up from {prev_label} to {last_label}"
        )
    if changes_last_two["down"]:
        parts_last_two.append(
            f"{', '.join(changes_last_two['down'])} went down from {prev_label} to {last_label}"
        )
    if changes_last_two["stable"]:
        parts_last_two.append(
            f"{', '.join(changes_last_two['stable'])} stayed at a similar level"
        )

    sentence_last_two = "; ".join(parts_last_two) + "." if parts_last_two else (
        f"There are only small changes between {prev_label} and {last_label}."
    )

    # Text across all months
    parts_all = []
    if trends_all["up"]:
        parts_all.append(
            f"over all months, {', '.join(trends_all['up'])} show a general increase"
        )
    if trends_all["down"]:
        parts_all.append(
            f"{', '.join(trends_all['down'])} move slightly down when we compare {first_label} and {final_label}"
        )
    if trends_all["mixed"]:
        parts_all.append(
            f"{', '.join(trends_all['mixed'])} move in a more irregular way, with some stronger and weaker months"
        )

    sentence_all = "; ".join(parts_all) + "." if parts_all else (
        "Across all months, the metrics move in different ways without one clear pattern."
    )

    return (
        f"For {network_name}, when we compare the last two available months "
        f"({prev_label} and {last_label}), {sentence_last_two} "
        f"Looking at all months, {sentence_all}"
    )


def show_key_insights(df: pd.DataFrame, network_name: str):
    st.markdown("**📌 Key insights**")
    insight_text = generate_insight_text(df, network_name)
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

    # Text stays below the chart, as before
    show_key_insights(df, network_name)

    with st.expander("Show data table"):
        st.dataframe(df)


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
