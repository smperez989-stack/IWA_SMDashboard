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
    default_path = "IWA SM Analytics.xlsx"
    try:
        data_dict = load_data(default_path)
        st.sidebar.success(f"Using local file: {default_path}")
    except Exception:
        st.sidebar.error("No file uploaded and default file not found.")
        st.stop()


# =========================================
# 4. Highlight last two months (NEW)
# =========================================
def highlight_last_two_months(fig, df: pd.DataFrame):

    df = df.dropna(subset=["Date"]).sort_values("Date").copy()

    if len(df["Date"].unique()) < 2:
        return fig

    last_two_dates = sorted(df["Date"].unique())[-2:]
    last_two_dates = [pd.Timestamp(d) for d in last_two_dates]

    highlight_colors = [
        "rgba(255,193,7,0.18)",   # second to last month
        "rgba(220,53,69,0.15)"    # last month
    ]

    for i, date_value in enumerate(last_two_dates):

        start_date = pd.Timestamp(date_value).replace(day=1)
        end_date = start_date + pd.offsets.MonthBegin(1)

        fig.add_vrect(
            x0=start_date,
            x1=end_date,
            fillcolor=highlight_colors[i],
            opacity=0.35,
            layer="below",
            line_width=0
        )

    return fig


# =========================================
# 5. Insight text generator
# =========================================
def generate_insight_text(df: pd.DataFrame, network_name: str):

    metrics = ["Followers", "Views", "Posts", "Interactions", "Comments"]

    df_sorted = df.dropna(subset=["Date"]).sort_values("Date")

    if len(df_sorted["Date"].unique()) < 2:
        return f"For {network_name}, there is not enough data yet to compare the last two months."

    last_two_dates = sorted(df_sorted["Date"].unique())[-2:]

    prev_row = df_sorted[df_sorted["Date"] == last_two_dates[0]].iloc[-1]
    last_row = df_sorted[df_sorted["Date"] == last_two_dates[1]].iloc[-1]

    prev_label = pd.Timestamp(last_two_dates[0]).strftime("%B %Y")
    last_label = pd.Timestamp(last_two_dates[1]).strftime("%B %Y")

    changes = {"up": [], "down": [], "stable": []}

    for metric in metrics:

        if metric in df_sorted.columns:

            prev_val = prev_row[metric]
            last_val = last_row[metric]

            if last_val > prev_val:
                changes["up"].append(metric.lower())

            elif last_val < prev_val:
                changes["down"].append(metric.lower())

            else:
                changes["stable"].append(metric.lower())

    parts = []

    if changes["up"]:
        parts.append(
            f"{', '.join(changes['up'])} increased from {prev_label} to {last_label}"
        )

    if changes["down"]:
        parts.append(
            f"{', '.join(changes['down'])} decreased from {prev_label} to {last_label}"
        )

    if changes["stable"]:
        parts.append(
            f"{', '.join(changes['stable'])} remained stable"
        )

    sentence = "; ".join(parts) + "." if parts else (
        f"There are only small changes between {prev_label} and {last_label}."
    )

    return f"For {network_name}, when we compare the last two months ({prev_label} and {last_label}), {sentence}"


def show_key_insights(df: pd.DataFrame, network_name: str):

    st.markdown("**📌 Key insights**")

    insight_text = generate_insight_text(df, network_name)

    st.markdown(insight_text)


# =========================================
# 6. Helper to plot one social network
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

    # NEW → highlight the last two months
    fig = highlight_last_two_months(fig, df)

    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Value",
        legend_title="Metric",
        hovermode="x unified"
    )

    st.plotly_chart(fig, use_container_width=True)

    show_key_insights(df, network_name)

    with st.expander("Show data table"):
        st.dataframe(df)


# =========================================
# 7. Color palettes por red social
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
# 8. Dashboard layout
# =========================================

st.header("📊 Overall Summary")

st.markdown("""
**Facebook**  
Facebook stays quite stable from month to month.

**Instagram**  
Instagram is the most dynamic platform.

**LinkedIn**  
LinkedIn grows slowly but steadily.

**Overall**  
Instagram has the highest movement.  
Facebook is stable.  
LinkedIn supports the professional image of IWA.
""")

st.markdown("---")

st.header("📘 Facebook")
show_network_section("Facebook", data_dict["Facebook"], color_sequence=facebook_colors)

st.markdown("---")

st.header("📷 Instagram")
show_network_section("Instagram", data_dict["Instagram"], color_sequence=instagram_colors)

st.markdown("---")

st.header("💼 LinkedIn")
show_network_section("LinkedIn", data_dict["LinkedIn"], color_sequence=linkedin_colors)
