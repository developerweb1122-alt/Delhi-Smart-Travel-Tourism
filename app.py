import streamlit as st
import pandas as pd
import requests
from pathlib import Path
from datetime import datetime, timedelta

# =========================================================
# DELHI SMART TOURISM SYSTEM
# =========================================================

st.set_page_config(
    page_title="Delhi Smart Tourism",
    page_icon="🏛️",
    layout="wide"
)

# -----------------------------
# Load Excel Dataset
# -----------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "Delhi_Smart_Tourism_50_Places(1).xlsx"

@st.cache_data
def load_data():
    df = pd.read_excel(DATA_FILE)

    # Clean important columns
    for col in ["rating", "review_count", "entry_fee", "latitude",
                "longitude", "visiting_duration"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    for col in ["place_name", "category", "description",
                "nearby_metro", "best_time"]:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str).str.strip()

    return df

try:
    df = load_data()
except Exception as e:
    st.error("Excel file load nahi ho rahi.")
    st.info(
        "app.py aur Delhi_Smart_Tourism_50_Places(1).xlsx ko same folder mein rakho."
    )
    st.code(str(e))
    st.stop()


# -----------------------------
# Helper functions
# -----------------------------
def recommend_places(data, preferred_time, min_rating, max_rating,
                     preferred_category, top_n=5):

    result = data.copy()

    result["category_clean"] = (
        result["category"].fillna("").astype(str).str.strip().str.lower()
    )
    result["best_time_clean"] = (
        result["best_time"].fillna("").astype(str).str.strip().str.lower()
    )
    result["rating"] = pd.to_numeric(result["rating"], errors="coerce")

    time = preferred_time.strip().lower()
    category = preferred_category.strip().lower()

    filtered = result[
        (result["rating"] >= min_rating) &
        (result["rating"] <= max_rating) &
        (result["category_clean"] == category) &
        (result["best_time_clean"].str.contains(time, na=False))
    ]

    filtered = filtered.sort_values(by="rating", ascending=False)
    filtered = filtered.head(top_n)

    return filtered.drop(
        columns=["category_clean", "best_time_clean"],
        errors="ignore"
    )


def recommendation_score(data, preferred_time, min_rating, max_rating,
                          preferred_category):

    result = data.copy()

    result["rating"] = pd.to_numeric(result["rating"], errors="coerce")
    result["category_clean"] = (
        result["category"].fillna("").astype(str).str.strip().str.lower()
    )
    result["best_time_clean"] = (
        result["best_time"].fillna("").astype(str).str.strip().str.lower()
    )

    time = preferred_time.strip().lower()
    category = preferred_category.strip().lower()

    result["rating_score"] = result["rating"].apply(
        lambda x: 3 if pd.notna(x) and min_rating <= x <= max_rating else 0
    )

    result["time_score"] = result["best_time_clean"].apply(
        lambda x: 3 if time in x else 0
    )

    result["category_score"] = result["category_clean"].apply(
        lambda x: 3 if x == category else 0
    )

    result["rating_bonus"] = result["rating"].apply(
        lambda x: 1 if pd.notna(x) and x >= 4.5 else 0
    )

    result["total_score"] = (
        result["rating_score"] +
        result["time_score"] +
        result["category_score"] +
        result["rating_bonus"]
    )

    result = result.sort_values(
        by=["total_score", "rating"],
        ascending=[False, False]
    ).head(5)

    result.insert(0, "Rank", range(1, len(result) + 1))

    return result.drop(
        columns=[
            "category_clean", "best_time_clean",
            "rating_score", "time_score",
            "category_score", "rating_bonus"
        ],
        errors="ignore"
    )


def weather_condition(code):
    mapping = {
        0: "Clear Sky",
        1: "Cloudy",
        2: "Cloudy",
        3: "Cloudy",
        45: "Foggy",
        48: "Foggy",
        51: "Drizzle",
        53: "Drizzle",
        55: "Drizzle",
        56: "Drizzle",
        57: "Drizzle",
        61: "Rainy",
        63: "Rainy",
        65: "Rainy",
        66: "Rainy",
        67: "Rainy",
        71: "Snowy",
        73: "Snowy",
        75: "Snowy",
        77: "Snowy",
        80: "Rain Showers",
        81: "Rain Showers",
        82: "Rain Showers",
        95: "Thunderstorm",
        96: "Thunderstorm",
        99: "Thunderstorm"
    }
    return mapping.get(code, "Moderate")


def weather_suitability(condition):
    if condition in ["Clear Sky", "Cloudy"]:
        return "Good", "Sightseeing ke liye suitable."
    if condition in ["Drizzle", "Rain Showers"]:
        return "Moderate", "Umbrella ya covered places consider karein."
    if condition in ["Rainy", "Thunderstorm", "Snowy"]:
        return "Poor", "Outdoor sightseeing avoid karna better hai."
    if condition == "Foggy":
        return "Moderate", "Visibility kam ho sakti hai."
    return "Moderate", "Weather conditions check karein."


@st.cache_data(ttl=600)
def get_weather():
    latitude = 28.6139
    longitude = 77.2090

    url = (
        "https://api.open-meteo.com/v1/forecast"
        "?latitude=28.6139"
        "&longitude=77.2090"
        "&current=temperature_2m,weather_code"
        "&timezone=Asia%2FKolkata"
    )

    response = requests.get(url, timeout=10)
    response.raise_for_status()

    data = response.json()

    temperature = data["current"]["temperature_2m"]
    code = data["current"]["weather_code"]

    return temperature, code


def smart_recommendation(data, preferred_time, min_rating, max_rating,
                         preferred_category, condition):

    result = data.copy()

    result["rating"] = pd.to_numeric(result["rating"], errors="coerce")

    result["category_clean"] = (
        result["category"].fillna("").astype(str).str.strip().str.lower()
    )

    result["best_time_clean"] = (
        result["best_time"].fillna("").astype(str).str.strip().str.lower()
    )

    time = preferred_time.strip().lower()
    category = preferred_category.strip().lower()

    result["rating_score"] = result["rating"].apply(
        lambda x: 3 if pd.notna(x) and min_rating <= x <= max_rating else 0
    )

    result["time_score"] = result["best_time_clean"].apply(
        lambda x: 3 if time in x else 0
    )

    result["category_score"] = result["category_clean"].apply(
        lambda x: 3 if x == category else 0
    )

    result["rating_bonus"] = result["rating"].apply(
        lambda x: 1 if pd.notna(x) and x >= 4.5 else 0
    )

    weather_score = {
        "Good": 3,
        "Moderate": 1,
        "Poor": 0
    }.get(condition, 1)

    result["weather_score"] = weather_score
    result["smart_score"] = (
        result["rating_score"] +
        result["time_score"] +
        result["category_score"] +
        result["rating_bonus"] +
        result["weather_score"]
    )

    result = result.sort_values(
        by=["smart_score", "rating"],
        ascending=[False, False]
    ).head(5)

    return result.drop(
        columns=[
            "category_clean", "best_time_clean",
            "rating_score", "time_score",
            "category_score", "rating_bonus",
            "weather_score"
        ],
        errors="ignore"
    )


def make_itinerary(data, selected_categories, selected_time,
                   min_rating, days, max_minutes_per_day):

    working = data.copy()
    working["rating"] = pd.to_numeric(working["rating"], errors="coerce")
    working["visiting_duration"] = pd.to_numeric(
        working["visiting_duration"], errors="coerce"
    )

    if selected_categories:
        working = working[
            working["category"].isin(selected_categories)
        ]

    if selected_time != "Any":
        working = working[
            working["best_time"].str.contains(
                selected_time, case=False, na=False
            )
        ]

    working = working[working["rating"] >= min_rating]
    working = working.sort_values(
        by=["rating", "review_count"],
        ascending=[False, False]
    )

    used = set()
    itinerary = []

    for day in range(1, days + 1):
        day_places = []
        total_minutes = 0

        for idx, row in working.iterrows():
            if idx in used:
                continue

            duration = row["visiting_duration"]

            if pd.isna(duration):
                duration = 60

            if total_minutes + duration <= max_minutes_per_day:
                day_places.append(row)
                used.add(idx)
                total_minutes += duration

            if len(day_places) >= 5:
                break

        if day_places:
            itinerary.append((day, day_places, total_minutes))

    return itinerary


# =========================================================
# SIDEBAR
# =========================================================
st.sidebar.title("🏛️ Delhi Smart Tourism")

page = st.sidebar.radio(
    "Select Module",
    [
        "Home",
        "Explore Delhi",
        "Place Recommendation",
        "Recommendation Engine",
        "Budget Planner",
        "AI Itinerary Planner",
        "Live Weather",
        "AI Travel Chatbot"
    ]
)

st.sidebar.markdown("---")
st.sidebar.caption("AI Based Smart Tourism System – Delhi")


# =========================================================
# HOME
# =========================================================
if page == "Home":

    st.title("🏛️ Delhi Smart Tourism System")
    st.subheader("AI Based Smart Tourism System – Delhi")

    st.write(
        "Delhi ke tourist places ko explore, filter aur recommend karne "
        "ke liye ek integrated tourism platform."
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Tourist Places", len(df))
    c2.metric("Categories", df["category"].nunique())
    c3.metric("Average Rating", round(df["rating"].mean(), 2))
    c4.metric("Free Places", int((df["entry_fee"] == 0).sum()))

    st.markdown("---")

    st.info(
        "👈 Sidebar se koi bhi module select karke website use karein."
    )

    st.markdown("### Available Modules")
    st.write("""
    - 🔎 Explore Delhi
    - 🎯 Place Recommendation
    - 🧠 Recommendation Engine
    - 💰 Budget Planner
    - 🗓️ AI Itinerary Planner
    - 🌤️ Live Weather
    - 💬 AI Travel Chatbot
    """)


# =========================================================
# EXPLORE DELHI
# =========================================================
elif page == "Explore Delhi":

    st.title("🔎 Explore Delhi")

    col1, col2 = st.columns(2)

    with col1:
        search = st.text_input(
            "Search Place",
            placeholder="Example: Red Fort"
        )

    with col2:
        categories = ["All"] + sorted(
            df["category"].dropna().unique().tolist()
        )
        category_filter = st.selectbox(
            "Category",
            categories
        )

    col3, col4 = st.columns(2)

    with col3:
        min_rating_filter = st.slider(
            "Minimum Rating",
            0.0, 5.0, 0.0, 0.1
        )

    with col4:
        max_fee = st.number_input(
            "Maximum Entry Fee (₹)",
            min_value=0,
            value=1000,
            step=50
        )

    filtered = df.copy()

    if search:
        filtered = filtered[
            filtered["place_name"].str.contains(
                search, case=False, na=False
            )
        ]

    if category_filter != "All":
        filtered = filtered[
            filtered["category"] == category_filter
        ]

    filtered = filtered[filtered["rating"] >= min_rating_filter]
    filtered = filtered[filtered["entry_fee"] <= max_fee]

    st.write(f"**{len(filtered)} places found**")

    st.dataframe(
        filtered[
            [
                "place_name", "category", "rating",
                "entry_fee", "opening_time",
                "closing_time", "visiting_duration",
                "nearby_metro", "best_time"
            ]
        ],
        use_container_width=True,
        hide_index=True
    )

    if not filtered.empty:
        st.subheader("📍 Tourist Places Map")
        map_df = filtered[["latitude", "longitude"]].dropna()
        if not map_df.empty:
            st.map(map_df)


# =========================================================
# PLACE RECOMMENDATION
# =========================================================
elif page == "Place Recommendation":

    st.title("🎯 Place Recommendation")

    st.write(
        "Apni preferred time, rating aur category enter karke "
        "matching tourist places dekhein."
    )

    col1, col2 = st.columns(2)

    with col1:
        preferred_time = st.selectbox(
            "Preferred Time",
            ["Morning", "Afternoon", "Evening"]
        )

        min_rating = st.number_input(
            "Minimum Rating",
            min_value=0.0,
            max_value=5.0,
            value=4.0,
            step=0.1
        )

    with col2:
        max_rating = st.number_input(
            "Maximum Rating",
            min_value=0.0,
            max_value=5.0,
            value=5.0,
            step=0.1
        )

        category_list = sorted(
            df["category"].dropna().unique().tolist()
        )

        preferred_category = st.selectbox(
            "Preferred Category",
            category_list
        )

    if st.button("🎯 Get Recommendations", type="primary"):

        if min_rating > max_rating:
            st.error("Minimum rating maximum rating se zyada nahi ho sakti.")
        else:
            result = recommend_places(
                df,
                preferred_time,
                min_rating,
                max_rating,
                preferred_category,
                top_n=5
            )

            if result.empty:
                st.warning(
                    "Exact preferences ke according koi place nahi mila."
                )
            else:
                st.success("Top matching places:")
                st.dataframe(
                    result,
                    use_container_width=True,
                    hide_index=True
                )


# =========================================================
# RECOMMENDATION ENGINE
# =========================================================
elif page == "Recommendation Engine":

    st.title("🧠 Recommendation Engine")

    st.write(
        "Yeh module rating, preferred time aur category ke basis par "
        "score calculate karke top 5 places rank karta hai."
    )

    col1, col2 = st.columns(2)

    with col1:
        engine_time = st.selectbox(
            "Preferred Time",
            ["Morning", "Afternoon", "Evening"],
            key="engine_time"
        )

        engine_min_rating = st.number_input(
            "Minimum Rating",
            0.0, 5.0, 4.0, 0.1,
            key="engine_min_rating"
        )

    with col2:
        engine_max_rating = st.number_input(
            "Maximum Rating",
            0.0, 5.0, 5.0, 0.1,
            key="engine_max_rating"
        )

        engine_category = st.selectbox(
            "Category",
            sorted(df["category"].dropna().unique().tolist()),
            key="engine_category"
        )

    if st.button("🧠 Generate Ranking", type="primary"):

        result = recommendation_score(
            df,
            engine_time,
            engine_min_rating,
            engine_max_rating,
            engine_category
        )

        st.subheader("Top 5 Recommended Places")

        if result.empty:
            st.warning("No results found.")
        else:
            st.dataframe(
                result,
                use_container_width=True,
                hide_index=True
            )


# =========================================================
# BUDGET PLANNER
# =========================================================
elif page == "Budget Planner":

    st.title("💰 Budget Planner")

    st.write(
        "Yahan tourist places ki entry fees ke saath aap apne "
        "food, transport, hotel aur other expenses add karke "
        "estimated trip budget calculate kar sakte hain."
    )

    col1, col2 = st.columns(2)

    with col1:
        people = st.number_input(
            "Number of People",
            min_value=1,
            value=1,
            step=1
        )

        days = st.number_input(
            "Number of Days",
            min_value=1,
            value=1,
            step=1
        )

        selected_places = st.multiselect(
            "Select Tourist Places",
            df["place_name"].tolist()
        )

    with col2:
        food_per_person_day = st.number_input(
            "Food Cost per Person / Day (₹)",
            min_value=0,
            value=500,
            step=100
        )

        transport_per_day = st.number_input(
            "Transport Cost per Day (₹)",
            min_value=0,
            value=300,
            step=100
        )

        hotel_per_day = st.number_input(
            "Hotel Cost per Day (₹)",
            min_value=0,
            value=1000,
            step=100
        )

        other_cost = st.number_input(
            "Other Cost (₹)",
            min_value=0,
            value=0,
            step=100
        )

    if st.button("💰 Calculate Budget", type="primary"):

        selected_df = df[
            df["place_name"].isin(selected_places)
        ]

        entry_fee_per_person = selected_df["entry_fee"].fillna(0).sum()

        entry_fee_total = entry_fee_per_person * people

        food_total = food_per_person_day * people * days
        transport_total = transport_per_day * days
        hotel_total = hotel_per_day * days
        total = (
            entry_fee_total +
            food_total +
            transport_total +
            hotel_total +
            other_cost
        )

        c1, c2, c3, c4 = st.columns(4)

        c1.metric("Entry Fees", f"₹{entry_fee_total:,.0f}")
        c2.metric("Food", f"₹{food_total:,.0f}")
        c3.metric("Transport + Hotel",
                  f"₹{transport_total + hotel_total:,.0f}")
        c4.metric("Estimated Total", f"₹{total:,.0f}")

        st.markdown("---")

        budget_table = pd.DataFrame({
            "Expense": [
                "Entry Fees",
                "Food",
                "Transport",
                "Hotel",
                "Other"
            ],
            "Amount (₹)": [
                entry_fee_total,
                food_total,
                transport_total,
                hotel_total,
                other_cost
            ]
        })

        st.dataframe(
            budget_table,
            use_container_width=True,
            hide_index=True
        )


# =========================================================
# AI ITINERARY PLANNER
# =========================================================
elif page == "AI Itinerary Planner":

    st.title("🗓️ AI Itinerary Planner")

    st.write(
        "Selected preferences aur visiting duration ke basis par "
        "day-wise trip plan generate hota hai."
    )

    col1, col2 = st.columns(2)

    with col1:
        itinerary_days = st.number_input(
            "Trip Days",
            min_value=1,
            max_value=10,
            value=1,
            step=1
        )

        itinerary_categories = st.multiselect(
            "Preferred Categories",
            sorted(df["category"].dropna().unique().tolist())
        )

    with col2:
        itinerary_time = st.selectbox(
            "Preferred Time",
            ["Any", "Morning", "Afternoon", "Evening"],
            key="itinerary_time"
        )

        itinerary_rating = st.number_input(
            "Minimum Rating",
            0.0, 5.0, 4.0, 0.1,
            key="itinerary_rating"
        )

    max_minutes = st.number_input(
        "Maximum Sightseeing Minutes per Day",
        min_value=60,
        max_value=720,
        value=360,
        step=30
    )

    if st.button("🗓️ Generate Itinerary", type="primary"):

        plan = make_itinerary(
            df,
            itinerary_categories,
            itinerary_time,
            itinerary_rating,
            int(itinerary_days),
            max_minutes
        )

        if not plan:
            st.warning(
                "Given preferences ke according itinerary generate nahi ho payi."
            )
        else:
            for day, places, total_minutes in plan:

                st.subheader(
                    f"📅 Day {day} — Approx. {int(total_minutes)} minutes"
                )

                for i, place in enumerate(places, 1):

                    with st.container(border=True):

                        st.markdown(
                            f"### {i}. {place['place_name']}"
                        )

                        c1, c2, c3 = st.columns(3)

                        c1.write(f"⭐ Rating: {place['rating']}")
                        c2.write(f"💰 Entry Fee: ₹{place['entry_fee']}")
                        c3.write(
                            f"⏱️ Duration: {place['visiting_duration']} min"
                        )

                        st.write(
                            f"**Category:** {place['category']}  |  "
                            f"**Best Time:** {place['best_time']}"
                        )

                        st.write(
                            f"🚇 **Nearby Metro:** {place['nearby_metro']}"
                        )


# =========================================================
# LIVE WEATHER
# =========================================================
elif page == "Live Weather":

    st.title("🌤️ Live Delhi Weather")

    st.write(
        "Delhi ke liye current weather Open-Meteo service se fetch kiya jata hai."
    )

    if st.button("🌤️ Check Current Weather", type="primary"):

        try:
            temperature, code = get_weather()
            condition = weather_condition(code)
            suitability, advice = weather_suitability(condition)

            c1, c2, c3 = st.columns(3)

            c1.metric("Temperature", f"{temperature} °C")
            c2.metric("Condition", condition)
            c3.metric("Sightseeing", suitability)

            if suitability == "Good":
                st.success(advice)
            elif suitability == "Moderate":
                st.warning(advice)
            else:
                st.error(advice)

        except Exception as e:
            st.error(
                "Weather data abhi fetch nahi ho pa raha. "
                "Internet connection check karein."
            )
            st.caption(str(e))


# =========================================================
# AI TRAVEL CHATBOT
# =========================================================
elif page == "AI Travel Chatbot":

    st.title("💬 AI Travel Chatbot")

    st.write(
        "Delhi tourism dataset ke basis par aap place, category, "
        "rating, fee, metro aur timing ke baare mein pooch sakte hain."
    )

    question = st.text_input(
        "Ask your question",
        placeholder="Example: Which places are free?"
    )

    if st.button("💬 Ask", type="primary"):

        q = question.lower().strip()

        if not q:
            st.warning("Please enter a question.")
            st.stop()

        # Free places
        if "free" in q or "no fee" in q or "without fee" in q:

            result = df[df["entry_fee"] == 0].sort_values(
                "rating", ascending=False
            )

            st.success(f"{len(result)} free places found.")
            st.dataframe(
                result[
                    ["place_name", "category", "rating", "best_time"]
                ],
                use_container_width=True,
                hide_index=True
            )

        # Highest rated
        elif "highest rating" in q or "top rated" in q:

            result = df.sort_values(
                ["rating", "review_count"],
                ascending=[False, False]
            ).head(5)

            st.write("### Top Rated Places")
            st.dataframe(
                result[
                    ["place_name", "category", "rating", "review_count"]
                ],
                use_container_width=True,
                hide_index=True
            )

        # Cheapest
        elif "cheap" in q or "cheapest" in q or "low fee" in q:

            result = df.sort_values(
                ["entry_fee", "rating"],
                ascending=[True, False]
            ).head(10)

            st.write("### Cheapest Places")
            st.dataframe(
                result[
                    ["place_name", "category", "entry_fee", "rating"]
                ],
                use_container_width=True,
                hide_index=True
            )

        # Morning
        elif "morning" in q:

            result = df[
                df["best_time"].str.contains(
                    "Morning", case=False, na=False
                )
            ].sort_values("rating", ascending=False).head(10)

            st.write("### Morning Suitable Places")
            st.dataframe(
                result[
                    ["place_name", "category", "rating", "entry_fee",
                     "nearby_metro"]
                ],
                use_container_width=True,
                hide_index=True
            )

        # Evening
        elif "evening" in q:

            result = df[
                df["best_time"].str.contains(
                    "Evening", case=False, na=False
                )
            ].sort_values("rating", ascending=False).head(10)

            st.write("### Evening Suitable Places")
            st.dataframe(
                result[
                    ["place_name", "category", "rating", "entry_fee",
                     "nearby_metro"]
                ],
                use_container_width=True,
                hide_index=True
            )

        # Specific place
        else:

            matched = df[
                df["place_name"].str.lower().str.contains(
                    q, na=False
                )
            ]

            if not matched.empty:

                for _, place in matched.head(3).iterrows():

                    st.subheader(place["place_name"])

                    st.write(place["description"])

                    c1, c2, c3 = st.columns(3)

                    c1.write(f"⭐ Rating: {place['rating']}")
                    c2.write(f"💰 Entry Fee: ₹{place['entry_fee']}")
                    c3.write(
                        f"⏱️ Duration: {place['visiting_duration']} min"
                    )

                    st.write(
                        f"**Category:** {place['category']}  |  "
                        f"**Best Time:** {place['best_time']}"
                    )

                    st.write(
                        f"🚇 **Nearby Metro:** {place['nearby_metro']}"
                    )

            else:

                # Category question
                category_matches = [
                    cat for cat in df["category"].unique()
                    if cat and cat.lower() in q
                ]

                if category_matches:

                    cat = category_matches[0]

                    result = df[
                        df["category"].str.lower() == cat.lower()
                    ].sort_values(
                        "rating", ascending=False
                    ).head(10)

                    st.write(f"### {cat} Places")

                    st.dataframe(
                        result[
                            ["place_name", "rating",
                             "entry_fee", "best_time"]
                        ],
                        use_container_width=True,
                        hide_index=True
                    )

                else:
                    st.info(
                        "Try questions like: "
                        "'Which places are free?', "
                        "'Top rated places', "
                        "'Cheapest places', "
                        "'Morning places', "
                        "'Evening places', "
                        "or enter a place name."
                    )


# =========================================================
# FOOTER
# =========================================================
st.markdown("---")
st.caption(
    "Delhi Smart Tourism System | MCA Project | "
    "Data-driven tourism recommendation platform"
)
