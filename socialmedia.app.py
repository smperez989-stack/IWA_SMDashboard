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
# =========================================
def generate_insight_text(df, network_name):
    # Filtrar solo Octubre y Noviembre
    df_subset = df[df["Month"].isin(["October", "November"])]

    if df_subset["Month"].nunique() < 2:
        return (
            f"For **{network_name}**, more data is needed for both October and November "
            "to make a month-to-month comparison."
        )

    metrics = ["Followers", "Views", "Posts", "Interactions", "Comments"]

    changes_oct_nov = {"up": [], "down": [], "stable": []}

    for metric in metrics:
        if metric in df_subset.columns:
            oct_val = df_subset[df_subset["Month"] == "October"][metric].sum()
            nov_val = df_subset[df_subset["Month"] == "November"][metric].sum()

            if nov_val > oct_val:
                changes_oct_nov["up"].append(metric.lower())
            elif nov_val < oct_val:
                changes_oct_nov["down"].append(metric.lower())
            else:
                changes_oct_nov["stable"].append(metric.lower())

    # Tendencia general entre todos los meses (primer mes vs último mes)
    df_sorted = df.sort_values("Date")
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

    # Construir texto simple
    parts_oct_nov = []
    if changes_oct_nov["up"]:
        parts_oct_nov.append(
            f"{', '.join(changes_oct_nov['up'])} increased from October to November"
        )
    if changes_oct_nov["down"]:
        parts_oct_nov.append(
            f"{', '.join(changes_oct_nov['down'])} decreased from October to November"
        )
    if changes_oct_nov["stable"]:
        parts_oct_nov.append(
            f"{', '.join(changes_oct_nov['stable'])} stayed at a similar level"
        )

    if parts_oct_nov:
        sentence_oct_nov = "; ".join(parts_oct_nov) + "."
    else:
        sentence_oct_nov = (
            "There are only small changes between October and November across the metrics."
        )

    parts_all = []
    if trends_all["up"]:
        parts_all.append(
            f"over all months, {', '.join(trends_all['up'])} show a general upward trend"
        )
    if trends_all["down"]:
        parts_all.append(
            f"{', '.join(trends_all['down'])} move slightly down when we compare the first and last month"
        )
    if trends_all["mixed"]:
        parts_all.append(
            f"{', '.join(trends_all['mixed'])} move in a more irregular way, with some stronger and weaker months"
        )

    if parts_all:
        sentence_all = "; ".join(parts_all) + "."
    else:
        sentence_all = (
            "Across all months, the metrics move in a mixed way without a clear single trend."
        )

    text = (
        f"For **{network_name}**, when we compare October and November, "
        f"{sentence_oct_nov} "
        f"Looking at all the months in the dataset, {sentence_all}"
    )

    return text


def show_key_insights(df, network_name):
    st.subheader("📌 Key Insights: Monthly Patterns")

    insight_text = generate_insight_text(df, network_name)

    st.markdown(
        f"""
📝 **Short summary**

{insight_text}
        """
    )


# =========================================
# 5. Helper to plot one social network
# =========================================
def show_network_tab(network_name, df, color_sequence=None):
    st.subheader(network_name)

    metrics = ["Followers", "Views", "Posts", "Interactions", "Comments"]

    selected_metrics = st.multiselect(
        "Select metrics to display:",
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

    # Optional: show raw data
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
# 7. Tabs per social network
# =========================================
tab_fb, tab_ig, tab_li = st.tabs(["Facebook", "Instagram", "LinkedIn"])

with tab_fb:
    show_network_tab("Facebook", data_dict["Facebook"], color_sequence=facebook_colors)
    show_key_insights(data_dict["Facebook"], "Facebook")

with tab_ig:
    show_network_tab("Instagram", data_dict["Instagram"], color_sequence=instagram_colors)
    show_key_insights(data_dict["Instagram"], "Instagram")

with tab_li:
    show_network_tab("LinkedIn", data_dict["LinkedIn"], color_sequence=linkedin_colors)
    show_key_insights(data_dict["LinkedIn"], "LinkedIn")
