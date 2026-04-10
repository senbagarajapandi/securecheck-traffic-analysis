import streamlit as st
import pandas as pd
import mysql.connector

# -------------------------------
# DATABASE CONNECTION
# -------------------------------
def create_connection():
    try:
        return mysql.connector.connect(
            host="gateway01.ap-southeast-1.prod.aws.tidbcloud.com",
            port=4000,
            user="4DGFMLygZ8KUSn2.root",
            password="SS6uE22WnEnkQXjj",
            database="securecheck"
        )
    except Exception as e:
        st.error(f"Database error: {e}")
        return None

# -------------------------------
# FETCH DATA
# -------------------------------
def fetch_data(query):
    conn = create_connection()
    if conn is None:
        return pd.DataFrame()

    try:
        df = pd.read_sql(query, conn)
        df.index = df.index + 1   # ✅ INDEX FIX
        return df
    except Exception as e:
        st.error(f"Query error: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

# -------------------------------
# LOAD DATA
# -------------------------------
df = fetch_data("SELECT * FROM traffic_stops")

st.set_page_config(layout="wide")
st.title("SecureCheck: Police Check Post Digital Ledger")

if df.empty:
    st.error("Database not connected")
    st.stop()

# -------------------------------
# DATA VIEW
# -------------------------------
st.header("Dataset Overview")
st.dataframe(df)

# -------------------------------
# METRICS
# -------------------------------
st.header("Key Metrics")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Stops", df.shape[0])

with col2:
    total_warnings = df[df["stop_outcome"].astype(str).str.contains("warning", case=False)].shape[0]
    st.metric("Total Warnings", total_warnings)

with col3:
    total_arrests = df[df["stop_outcome"].astype(str).str.contains("arrest", case=False)].shape[0]
    st.metric("Total Arrests", total_arrests)

# -------------------------------
# QUERIES
# -------------------------------
st.header("Advanced Insights")

query_map = {

"top 10 vehicle_Number in drug-related stops":
"SELECT vehicle_number FROM traffic_stops WHERE drugs_related_stop=1 LIMIT 10",

"most frequently searched vehicles":
"SELECT vehicle_number, COUNT(*) as count FROM traffic_stops WHERE search_conducted=1 GROUP BY vehicle_number ORDER BY count DESC LIMIT 10",

"the highest arrest rate of driver age group":
"SELECT driver_age, COUNT(*) as arrests FROM traffic_stops WHERE is_arrested=1 GROUP BY driver_age ORDER BY arrests DESC LIMIT 10",

"the gender distribution of drivers stopped in each country":
"SELECT country_name, driver_gender, COUNT(*) as total FROM traffic_stops GROUP BY country_name, driver_gender",

"driver_race and gender combination has the highest search rate":
"SELECT driver_race, driver_gender, COUNT(*) as total FROM traffic_stops WHERE search_conducted=1 GROUP BY driver_race, driver_gender ORDER BY total DESC LIMIT 10",

"the time of day sees the most traffic stops":
"SELECT HOUR(stop_time) as hour, COUNT(*) as total FROM traffic_stops GROUP BY hour ORDER BY total DESC",

"the average stop duration for different violations":
"SELECT violation, AVG(stop_duration) as avg_duration FROM traffic_stops GROUP BY violation",

"stops during the night more likely to lead to arrests":
"SELECT stop_outcome, COUNT(*) FROM traffic_stops WHERE HOUR(stop_time) BETWEEN 0 AND 5 GROUP BY stop_outcome",

"the violations are most associated with searches or arrests":
"SELECT violation, COUNT(*) FROM traffic_stops WHERE search_conducted=1 OR is_arrested=1 GROUP BY violation ORDER BY COUNT(*) DESC",

"the violations are most common among younger drivers (<25)":
"SELECT violation, COUNT(*) FROM traffic_stops WHERE driver_age < 25 GROUP BY violation ORDER BY COUNT(*) DESC",

"a violation that rarely results in search or arrest":
"SELECT violation, COUNT(*) FROM traffic_stops WHERE search_conducted=0 AND is_arrested=0 GROUP BY violation ORDER BY COUNT(*) ASC LIMIT 10",

"the countries report the highest rate of drug-related stops":
"SELECT country_name, COUNT(*) FROM traffic_stops WHERE drugs_related_stop=1 GROUP BY country_name ORDER BY COUNT(*) DESC",

"the arrest rate by country and violation":
"SELECT country_name, violation, COUNT(*) FROM traffic_stops WHERE is_arrested=1 GROUP BY country_name, violation",

"the country has the most stops with search conducted":
"SELECT country_name, COUNT(*) FROM traffic_stops WHERE search_conducted=1 GROUP BY country_name ORDER BY COUNT(*) DESC",

"Yearly Breakdown of Stops and Arrests by Country":
"SELECT YEAR(stop_date) as year, country_name, COUNT(*) FROM traffic_stops GROUP BY year, country_name",

"Driver Violation Trends Based on Age and Race":
"SELECT driver_age, driver_race, violation, COUNT(*) FROM traffic_stops GROUP BY driver_age, driver_race, violation",

"Time Period Analysis of Stops":
"SELECT HOUR(stop_time) as hour, COUNT(*) FROM traffic_stops GROUP BY hour",

"Violations with High Search and Arrest Rates":
"SELECT violation, COUNT(*) FROM traffic_stops WHERE search_conducted=1 OR is_arrested=1 GROUP BY violation ORDER BY COUNT(*) DESC",

"Driver Demographics by Country":
"SELECT country_name, driver_gender, driver_race, COUNT(*) FROM traffic_stops GROUP BY country_name, driver_gender, driver_race",

"Top 5 Violations with Highest Arrest Rates":
"SELECT violation, COUNT(*) FROM traffic_stops WHERE is_arrested=1 GROUP BY violation ORDER BY COUNT(*) DESC LIMIT 5"

}

selected_query = st.selectbox("Select Query", list(query_map.keys()))

if st.button("Run Query"):
    result = fetch_data(query_map[selected_query])
    if not result.empty:
        st.dataframe(result)
    else:
        st.warning("No results found")

# -------------------------------
# FORM
# -------------------------------
st.header("Add New Police Log")

with st.form("new_log_form"):
    stop_date = st.date_input("Stop Date")
    stop_time = st.time_input("Stop Time")
    country_name = st.text_input("Country Name")
    driver_gender = st.selectbox("Driver Gender", ["Male", "Female"])
    driver_age = st.number_input("Driver Age", 16, 100, 27)
    driver_race = st.text_input("Driver Race")
    search_conducted = st.selectbox("Search Conducted", [0, 1])
    search_type = st.text_input("Search Type")
    drugs_related_stop = st.selectbox("Drug Related Stop", [0, 1])
    stop_duration = st.selectbox("Stop Duration", df["stop_duration"].dropna().unique())
    vehicle_number = st.text_input("Vehicle Number")

    submitted = st.form_submit_button("Predict")

    if submitted:
        filtered = df[
            (df['driver_gender'] == driver_gender) &
            (df['driver_age'] == driver_age) &
            (df['search_conducted'] == search_conducted) &
            (df['drugs_related_stop'] == drugs_related_stop)
        ]

        if not filtered.empty:
            outcome = filtered['stop_outcome'].mode()[0]
            violation = filtered['violation'].mode()[0]
        else:
            outcome = "Warning"
            violation = "Speeding"

        # Convert values to readable format
gender_text = driver_gender.lower()
search_text = "A search was conducted" if search_conducted == 1 else "No search was conducted"
drug_text = "was drug-related" if drugs_related_stop == 1 else "was not drug-related"

# Format time
formatted_time = stop_time.strftime("%I:%M %p")

st.success("Prediction Result")

st.markdown(f"""
A {driver_age}-year-old {gender_text} driver was stopped for **{violation}** at **{formatted_time}**.  

{search_text}, and the driver received a **{outcome}**.  

The stop lasted **{stop_duration}** and {drug_text}.
""")