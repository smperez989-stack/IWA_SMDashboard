import streamlit as st
import pandas as pd

df = pd.read_excel("IWA SM Analytics.xlsx")

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
#    - Option A: use file_uploader
#    - Option B: default file name in the same folder
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
# 4. Helper to plot one social network
# =========================================
def show_network_tab(network_name, df):
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

    plot_df = df[["Date"] + selected_metrics].set_index("Date")

    st.line_chart(plot_df)

    # Optional: show raw data
    with st.expander("Show data table"):
        st.dataframe(df)

# =========================================
# 5. Tabs per social network
# =========================================
tab_fb, tab_ig, tab_li = st.tabs(["Facebook", "Instagram", "LinkedIn"])

with tab_fb:
    show_network_tab("Facebook", data_dict["Facebook"])

with tab_ig:
    show_network_tab("Instagram", data_dict["Instagram"])

with tab_li:
    show_network_tab("LinkedIn", data_dict["LinkedIn"])
