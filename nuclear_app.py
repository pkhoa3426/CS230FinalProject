"""
Name: Khoa Pham
CS230: Section 4
Data:  Nuclear Explosions 1945–1998
URL: [Add your Streamlit Cloud URL if published]

Description:
This interactive Streamlit application explores the nuclear explosions dataset from 1945–1998.
Users can filter by country and year range, analyze explosion magnitude and depth trends, and
view an interactive map of test sites.
"""

import streamlit as st
import pandas as pd
import pydeck as pdk
import matplotlib.pyplot as plt
import seaborn as sns
from PIL import Image

# ---- Page Setup ----
st.set_page_config(page_title="Nuclear Explosions Explorer", layout="wide")

@st.cache_data
def load_data():
    try:
        df = pd.read_csv("nuclear_explosions.csv")

        df = df.dropna(subset=[
            "Location.Cordinates.Latitude",
            "Location.Cordinates.Longitude",
            "Date.Day",
            "Date.Month",
            "Date.Year",
            "WEAPON SOURCE COUNTRY",
            "WEAPON DEPLOYMENT LOCATION",
            "Location.Cordinates.Depth",
            "Data.Purpose",
            "Data.Name",
            "Data.Type"
        ])

        df["Latitude"] = df["Location.Cordinates.Latitude"]
        df["Longitude"] = df["Location.Cordinates.Longitude"]
        df["Year"] = df["Date.Year"]
        df["Country"] = df["WEAPON SOURCE COUNTRY"]
        df["Depth"] = df["Location.Cordinates.Depth"]
        df["Location"] = df["WEAPON DEPLOYMENT LOCATION"] + ", " + df["Country"]
        df["Purpose"] = df["Data.Purpose"]
        df["Test Name"] = df["Data.Name"]
        df["Test Type"] = df["Data.Type"]
        df["Category"] = df["Test Type"]

        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

image = Image.open("banner.png")
st.image(image, use_container_width=True)

st.title("Nuclear Explosions Explorer")
st.markdown("Welcome to Khoa Pham's Nuclear Explosion Research App. Explore historical nuclear test data by country, depth, purpose, and type.")

data = load_data()

# ---- Navigation ----
section = st.sidebar.radio("Navigate", ["Overview", "Charts", "Map", "Details", "Feedback"])

# ---- Filters ----
st.sidebar.title("Filters")
countries = st.sidebar.multiselect("Select countries:", options=data["Country"].unique(), default=["USA", "USSR"])
year_range = st.sidebar.slider("Select year range:", int(data["Year"].min()), int(data["Year"].max()), (1960, 1980))

# Add "All" option to category filter
category_options = ["All"] + sorted(data["Category"].unique())
selected_categories = st.sidebar.multiselect("Select Categories:", options=category_options, default=["All"])

# ---- Search Bar ----
search = st.sidebar.text_input("Search by Test Name")

# ---- Filtering ----
if "All" in selected_categories:
    filtered_data = data[(data["Country"].isin(countries)) &
                         (data["Year"].between(year_range[0], year_range[1]))]
else:
    filtered_data = data[(data["Country"].isin(countries)) &
                         (data["Year"].between(year_range[0], year_range[1])) &
                         (data["Category"].isin(selected_categories))]

if search:
    filtered_data = filtered_data[filtered_data["Test Name"].str.contains(search, case=False, na=False)]

# ---- Sidebar Summary ----
count = filtered_data.shape[0]
if count > 0:
    avg_depth = filtered_data["Depth"].mean()
    min_depth = filtered_data["Depth"].min()
    max_depth = filtered_data["Depth"].max()
    avg_lat = filtered_data["Latitude"].mean()
    avg_lon = filtered_data["Longitude"].mean()
    unique_locations = filtered_data["Location"].nunique()
    top_country = filtered_data["Country"].value_counts().idxmax()
    top_purpose = filtered_data["Purpose"].value_counts().idxmax()
    top_type = filtered_data["Test Type"].value_counts().idxmax()

    with st.sidebar.expander("Data Summary", expanded=True):
        st.markdown(f"**# of Explosions:** {count}")
        st.markdown(f"**Avg Depth:** {avg_depth:.2f} m")
        st.markdown(f"**Min Depth:** {min_depth:.2f} m")
        st.markdown(f"**Max Depth:** {max_depth:.2f} m")
        st.markdown(f"**Avg Lat/Lon:** {avg_lat:.2f}, {avg_lon:.2f}")
        st.markdown(f"**Unique Test Sites:** {unique_locations}")
        st.markdown(f"**Most Tested Country:** {top_country}")
        st.markdown(f"**Most Common Purpose:** {top_purpose}")
        st.markdown(f"**Most Common Test Type:** {top_type}")
else:
    st.warning("No data matches the selected filters.")

# ---- Section Handling ----
if section == "Overview":
    st.header("Overview")
    st.write(f"Showing {filtered_data.shape[0]} explosions from {year_range[0]} to {year_range[1]}")

    if count > 0:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="Deepest Explosion (m)", value=f"{max_depth:.2f}")
        with col2:
            st.metric(label="Shallowest Explosion (m)", value=f"{min_depth:.2f}")
        with col3:
            top_year = filtered_data["Year"].value_counts().idxmax()
            top_year_count = filtered_data["Year"].value_counts().max()
            st.metric(label=f"Peak Year ({top_year})", value=f"{top_year_count} tests")

elif section == "Charts":
    if count > 1:
        st.header("Explosion Depth Distribution")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**About this chart:**\n\nThis histogram shows how deep each nuclear explosion occurred. It helps us understand testing patterns across test categories and countries.")
            fig1, ax1 = plt.subplots(figsize=(6, 4))
            sns.histplot(data=filtered_data, x="Depth", hue="Category", kde=True, ax=ax1)
            st.pyplot(fig1)

        with col2:
            st.markdown("**About this chart:**\n\nThis bar chart displays the number of nuclear tests conducted per year in the filtered range. It helps identify peak testing periods.")
            fig2, ax2 = plt.subplots(figsize=(6, 4))
            filtered_data["Year"].value_counts().sort_index().plot(kind='bar', ax=ax2)
            ax2.set_xlabel("Year")
            ax2.set_ylabel("# of Explosions")
            st.pyplot(fig2)
    else:
        st.warning("Not enough data to generate charts. Try adjusting your filters.")

elif section == "Map":
    if count > 0:
        st.header("Explosion Locations")
        st.markdown("This interactive map displays the geographical distribution of nuclear test sites. Each dot represents a test explosion site.")
        st.pydeck_chart(pdk.Deck(
            map_style="mapbox://styles/mapbox/light-v9",
            initial_view_state=pdk.ViewState(
                latitude=filtered_data["Latitude"].mean(),
                longitude=filtered_data["Longitude"].mean(),
                zoom=2,
                pitch=0,
            ),
            layers=[
                pdk.Layer(
                    "ScatterplotLayer",
                    data=filtered_data,
                    get_position='[Longitude, Latitude]',
                    get_color='[200, 30, 0, 160]',
                    get_radius=50000,
                    pickable=True,
                )
            ],
            tooltip={"text": "{Country}\n{Location}\nYear: {Year}\nDepth: {Depth}\nCategory: {Category}"}
        ))
    else:
        st.warning("No map data to display.")

elif section == "Details":
    if count > 0:
        st.header("Top 5 Deepest Explosions")
        st.markdown("This table shows the five deepest nuclear explosions based on filtered data.")
        st.dataframe(filtered_data.nlargest(5, "Depth")[["Country", "Location", "Year", "Depth", "Category"]])

        st.subheader("Explosion Test Details")
        st.markdown("A preview of key details for up to 10 nuclear tests matching your current filters.")
        st.dataframe(filtered_data[["Test Name", "Test Type", "Purpose", "Country", "Year", "Category"]].head(10))
    else:
        st.warning("No test details available for selected filters.")

elif section == "Feedback":
    st.header("User Feedback")
    with st.form("feedback_form"):
        name = st.text_input("Your Name (Optional):")
        rating = st.slider("How useful is this tool?", 1, 5, 3)
        comments = st.text_area("Additional Comments")
        submitted = st.form_submit_button("Submit Feedback")

    if submitted:
        st.success("Thank you for your feedback!")
        st.write("**Rating:**", rating)
        if name:
            st.write("**Submitted by:**", name)
        if comments:
            st.write("**Comment:**", comments)

