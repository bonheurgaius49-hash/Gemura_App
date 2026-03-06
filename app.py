import streamlit as st
import plotly.express as px
import pandas as pd
import os
import warnings
warnings.filterwarnings("ignore")

# Must be first Streamlit command
st.set_page_config(page_title="SA Beneficiaries", page_icon="logo.png", layout="wide")
# CSS for white paper, padding, rounded corners, black text
st.markdown("""
<style>
div.block-container{
    padding-left: 80px;
    padding-right: 80px;
    padding-top: 50px;
    padding-bottom: 50px;
    font-family: 'Arial', sans-serif;
}

/* Optional: style the header */
.dashboard-paper h1 {
    color: #c01e2e;
}
</style>
""", 
unsafe_allow_html=True
)

# Wrap content in the div with the class

DATA_PATH = "data"

# ------------------------------
# Define mappings
# ------------------------------
hospital_map = {
    0: "CHUK",
    1: "KIBAGABAGA",
    2: "MASAKA",
    3: "MUHIMA",
    4: "NYARUGENGE"
}

enumerator_map = {
    0: "Mugisha Honorine",
    1: "Batamuliza Annet",
    2: "Umuhoza Nathalie",
    3: "Umutoniwase Alliane",
    4: "Uwamahoro Gift",
    6: "Umuhoza Angelique",
    7: "Ahishakiye Marlene",
    8: "Tumukunde Deborah",
    9: "Barigye John"
}

diet_map = {
    1: "Pediatric care diet",
    2: "Post-Partum care diet",
    3: "Easy digest care diet",
    4: "High energy/protein care diet",
    5: "Sodium restricted/No salt diet",
    6: "Diabetic care diet",
    7: "IZERE/Pavillion/Other Private inpatient diets"
}

# ------------------------------
# Column names for CSV files
# ------------------------------
regular_cols = [
    "SubmissionDate", "starttime", "endtime", "deviceid", "devicephonenum", "username",
    "device_info", "duration", "caseid", "Date", "Enumerator", "Hospital",
    "BAT", "BST", "BET", "Breakfast", "LAT", "LST", "LET", "Lunch",
    "Male", "Female", "Female_caregivers", "Male_caregivers",
    "age_group_1", "age_group_2", "age_group_3", "age_group_4", "age_group_5",
    "Kigali", "South", "East", "North", "West",
    "DAT", "DST", "DET", "Dinner", "Challenge_satisfaction", "Recommendation",
    "Audio", "Image", "instanceID", "formdef_version", "KEY"
]

special_cols = [
    "SubmissionDate", "starttime", "endtime", "deviceid", "devicephonenum", "username",
    "device_info", "duration", "caseid", "Date", "Enumerator", "Hospital",
    "Diet", "Breakfast", "Lunch", "Male", "Female",
    "age_group_1", "age_group_2", "age_group_3", "age_group_4", "age_group_5",
    "Kigali", "South", "East", "North", "West",
    "Dinner", "instanceID", "formdef_version", "KEY"
]

regular = pd.read_csv(os.path.join(DATA_PATH, "Gemura Program (Normal diet) Database.csv"), header=0)
special = pd.read_csv(os.path.join(DATA_PATH, "Gemura Program (Special Diet) Database.csv"), header=0)

# Assign correct column names
regular.columns = regular_cols
special.columns = special_cols

# ------------------------------
# Load other Excel tables
# ------------------------------
hospitals = pd.read_excel(os.path.join(DATA_PATH, "Hospitals.xlsx"))
dates = pd.read_excel(os.path.join(DATA_PATH, "Date.xlsx"))
diet = pd.read_excel(os.path.join(DATA_PATH, "Diet.xlsx"))
Enumerators = pd.read_excel(os.path.join(DATA_PATH, "Enumerators.xlsx"))

# ------------------------------
# Clean column names
# ------------------------------
regular.columns = regular.columns.str.strip()
special.columns = special.columns.str.strip()

# ------------------------------
# Apply mappings
# ------------------------------
regular["Hospital"] = regular["Hospital"].map(hospital_map)
special["Hospital"] = special["Hospital"].map(hospital_map)

regular["Enumerator"] = regular["Enumerator"].map(enumerator_map)
special["Enumerator"] = special["Enumerator"].map(enumerator_map)

special["Diet"] = special["Diet"].map(diet_map)

# ------------------------------
# Convert Date columns
# ------------------------------
regular["Date"] = pd.to_datetime(regular["Date"])
special["Date"] = pd.to_datetime(special["Date"])

# Connect hospitals to regular and special
regular_merged = regular.merge(hospitals, on="Hospital", how="left")
special_merged = special.merge(hospitals, on="Hospital", how="left")

# Connect dates to regular and special
regular_merged = regular_merged.merge(dates, on="Date", how="left")
special_merged = special_merged.merge(dates, on="Date", how="left")

# Connect diet to special only
special_merged = special_merged.merge(diet, on="Diet", how="left")

import datetime
# ------------------------------
# Ensure Date is datetime
# ------------------------------
regular_merged["Date"] = pd.to_datetime(regular_merged["Date"])
special_merged["Date"] = pd.to_datetime(special_merged["Date"])

today = datetime.date.today()

yesterday = datetime.date.today() - datetime.timedelta(days=1)
st.markdown(
    f"""
    <div style='display:flex; align-items:center; justify-content:space-between; width:100%;'>
        <h1 style='color:#c01e2e; font-size:30px; margin:0;'>Gemura Program - Daily Beneficiaries To be Served</h1>
        <div style='font-size:18px; font-weight:bold;'>🗓️{datetime.date.today()}</div>
    </div>
    """,
    unsafe_allow_html=True
)
# ------------------------------
# Metric Calculation Function
# ------------------------------
def calculate_metric(df, hospital_name, diet_name=None):
    
    if diet_name:
        df_h = df[(df["Hospital"] == hospital_name) & (df["Diet"] == diet_name)].copy()
    else:
        df_h = df[df["Hospital"] == hospital_name].copy()
    
    df_h["Date_only"] = df_h["Date"].dt.date
    
    # --- TODAY DATA ---
    today_data = df_h[df_h["Date_only"] == yesterday]
    
    if not today_data.empty:
        value = today_data["Lunch"].sum()
        return round(value), False
    
    # --- 7-DAY AVERAGE (only days with submission) ---
    past_data = df_h[df_h["Date_only"] < yesterday]
    
    if past_data.empty:
        return 0, False
    
    # Group by date to get daily totals
    daily_totals = (
        past_data
        .groupby("Date_only")["Lunch"]
        .sum()
        .sort_index(ascending=False)
        .head(7)
    )
    
    if daily_totals.empty:
        return 0, False
    
    avg_value = daily_totals.mean()
    
    return round(avg_value), True

def get_yesterday_comments_per_hospital(df, hospital_list, date_to_check=yesterday):
    all_comments = []

    for hospital in hospital_list:
        df_h = df[df["Hospital"] == hospital].copy()
        df_h["Date_only"] = pd.to_datetime(df_h["Date"]).dt.date

        yesterday_data = df_h[df_h["Date_only"] == date_to_check]

        if yesterday_data.empty:
            combined_comments = "no comment"
        else:
            comments = yesterday_data["Challenge_satisfaction"].dropna()
            comments = comments[comments != 0]
            comments = comments[comments != "0"]
            comments = comments[comments.str.strip() != ""]

            if comments.empty:
                combined_comments = "no comment"
            else:
                comments_clean = comments.astype(str).str.replace(r"[\r\n]+", " ", regex=True).str.strip()
                combined_comments = " | ".join(comments_clean)

        # Choose color
        color = "#808080" if combined_comments == "no comment" else "#000000"

        hospital_comment_html = f"""
        <div style='padding:2px 5px; margin-bottom:0px; font-size:13px;'>
            <span style='font-weight:bold; color:#c01e2e;'>{hospital}:</span> 
            <span style='font-weight:normal; color:{color};'>{combined_comments}</span>
        </div>
        """
        all_comments.append(hospital_comment_html)

    return "<div>".join(all_comments)
# List of Hospitals
# ------------------------------
hospital_list = sorted(regular_merged["Hospital"].dropna().unique())

# ------------------------------
# CSS Styling for Cards
# ------------------------------
st.markdown("""
<style>
.hospital-card {
    background-color: white;
    padding: 0px;
    border-radius: 18px;
    box-shadow: 2px 4px 15px rgba(0,0,0,0.08);
    margin-bottom: 10px;
}
.hospital-title {
    color: #c01e2e;
    font-size: 22px;
    font-weight: bold;
    margin-bottom: 5px;
}
.metric-row {
    font-size: 12px;
    margin-bottom: 0px;
}
.caption {
    font-size: 13px;
    color: #777777;
    margin-left: 8px;
}
</style>
""", unsafe_allow_html=True)

# ------------------------------
# Responsive Layout (3 per row)
# ------------------------------

cols_per_row = 5

for i in range(0, len(hospital_list), cols_per_row):
    
    cols = st.columns(cols_per_row)
    
    for col, hospital in zip(cols, hospital_list[i:i+cols_per_row]):
        
        with col:

            regular_value, regular_avg = calculate_metric(regular_merged, hospital)
            postpartum, postpartum_avg = calculate_metric(special_merged, hospital, "Post-Partum care diet")
            pediatric, pediatric_avg = calculate_metric(special_merged, hospital, "Pediatric care diet")
            easy_digest, easy_avg = calculate_metric(special_merged, hospital, "Easy digest care diet")
            high_energy, high_avg = calculate_metric(special_merged, hospital, "High energy/protein care diet")
            diabetic, diabetic_avg = calculate_metric(special_merged, hospital, "Diabetic care diet")
            sodium, sodium_avg = calculate_metric(special_merged, hospital, "Sodium restricted/No salt diet")
            izere, izere_avg = calculate_metric(special_merged, hospital, "IZERE/Pavillion/Other Private inpatient diets")
            
            total_meals = (
                regular_value +
                postpartum +
                pediatric +
                easy_digest +
                high_energy +
                diabetic +
                sodium +
                izere
            )

            # 👇 RENDERING MUST STAY INSIDE HERE 👇

            def show_metric(label, value, avg_flag):
                caption = " <span style='color:#c01e2e;font-size:13px;'>*</span>" if avg_flag else ""
                label_html = f"<span style='color:#000000; padding-top:1px; font-size:12px;  border-top: 3px solid rgba(15, 23, 42, 0.5); margin-top:0px;'>{label}</span>"
                value_html = f"<span style='color:#000000;font-weight:bold; font-size:22px; margin-bottom:0px;'>{value}</span>"
                
                return f"<div class='metric-part' style='padding:2px;'>{value_html}{caption}<br>{label_html}</br></div>"
            
            # Collect all metric parts
            metric_parts = []
            metric_parts.append(show_metric("Regular Diet", regular_value, regular_avg))
            metric_parts.append(show_metric("Post-Partum", postpartum, postpartum_avg))
            metric_parts.append(show_metric("Pediatric", pediatric, pediatric_avg))
            metric_parts.append(show_metric("Easy digest", easy_digest, easy_avg))
            metric_parts.append(show_metric("High energy", high_energy, high_avg))
            metric_parts.append(show_metric("Diabetic", diabetic, diabetic_avg))
            metric_parts.append(show_metric("No salt", sodium, sodium_avg))
            metric_parts.append(show_metric("IZERE", izere, izere_avg))
            
            metrics_html = "".join(metric_parts)
            
            total_meals = f'<span style="font-size:25px; font-weight:bold; box-shadow: 2px 4px 15px rgba(0,0,0); color:#c01e2e; margin-top:0px; border:1px solid #c01e2e; padding-left:10px; padding-right:10px; border-radius:4px;">{total_meals}</span>'

            st.markdown(
                f"""
                <div class='hospital-card' style='padding:10px; border:2px solid #000000; border-radius:18px; background-color:#ffffff; margin-bottom:5px; box-shadow: 2px 4px 15px rgba(0,0,0);'>
                <div style='background-color:#f3f4f6; font-size:25px; color:#c01e2e; border-bottom: 3px solid rgba(15, 23, 42, 0.5); border-top: 3px solid rgba(15, 23, 42, 0.5);text-align:center; border-radius:10px; font-weight:bold; Padding:4px;'>{hospital}</div>
                <div style='display:grid; padding-left:4px; grid-template-columns: 1fr 1fr 1fr; gap:5px;'>{metrics_html}</div>
                <div style='text-align:center; margin-top:0px; margin-bottom:0px; padding:0px;'>TOTAL MEALS: {total_meals}</div>
                </div>
                """,
                unsafe_allow_html=True
                )
comments = get_yesterday_comments_per_hospital(regular_merged, hospital_list, yesterday) 
hospital_title_html = f"""
<div style="
    font-size:22px; 
    font-weight:bold; 
    color:#c01e2e; 
    text-align:center; 
    margin-bottom:10px;
">
    {hospital}
</div>
"""
comments = f"<div style='color:#000000; font-size:13px; font-weight:normal; padding:10px;'>{comments}</div>" if comments != "No comment" else "<span style='color:#8e8f91; font-size:12px; font-weight:normal; padding:10px;'>No comment</span>"

st.markdown(
    f"""
    <div style='padding:10px;'>
    <span style='margin-top:10px; font-size:14px; font-weight:bold; color:#777777; text-align:center;'>Comments/Recommendations: </span>
    <div style='border: 1px solid #000000; border-radius:4px;'>{comments}</div>
    </div>
    """,
    unsafe_allow_html=True
)
