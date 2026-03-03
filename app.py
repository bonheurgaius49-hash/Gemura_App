import streamlit as st
import plotly.express as px
import pandas as pd
import os
import warnings
warnings.filterwarnings("ignore")

# Must be first Streamlit command
st.set_page_config(page_title="Gemura Program Dashboard", page_icon="logo.png", layout="wide")
# CSS for white paper, padding, rounded corners, black text
st.markdown("""
<style>
div.block-container{
    padding-left: 100px;
    padding-right: 100px;
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
st.markdown("""
<div class="dashboard-paper">
    <h1>Beneficiaries Served by day</h1>
    <p>This dashboard tracks daily Lunch production for the Gemura Program across hospitals and diet categories. It updates dynamically by date and hospital, applies a 7-day average when submissions are missing, and highlights gaps in reporting to support performance monitoring.</p>

""", 
unsafe_allow_html=True
)

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

# ------------------------------
# Now regular_merged and special_merged have all connections
# ------------------------------
print("Regular merged shape:", regular_merged.shape)
print("Special merged shape:", special_merged.shape)
import streamlit as st

st.sidebar.image("Sidebar_image.png", width=250)
# Get unique hospitals from the merged table
hospital_options = sorted(regular_merged["Hospital"].dropna().unique())

# Add an "All Hospitals" option at the beginning
hospital_options = ["All Hospitals"] + hospital_options

# Sidebar dropdown
selected_hospital = st.sidebar.selectbox("Select Hospital", hospital_options)

# Filter based on selection
if selected_hospital == "All Hospitals":
    regular_filtered = regular_merged.copy()
    special_filtered = special_merged.copy()
else:
    regular_filtered = regular_merged[regular_merged["Hospital"] == selected_hospital]
    special_filtered = special_merged[special_merged["Hospital"] == selected_hospital]

# --- Date slicer ---
# --- Single Date slicer ---
min_date = regular_merged["Date"].min()
max_date = regular_merged["Date"].max()

selected_date = st.sidebar.date_input(
    "Select Date",
    value=min_date,       # default selected date
    min_value=min_date,
    max_value=max_date
)

# Ensure selected_date is a single date (not a tuple)
if isinstance(selected_date, tuple) or isinstance(selected_date, list):
    selected_date = selected_date[0]

selected_date = pd.to_datetime(selected_date)

# Example: Regular Diet filtered by hospital + selected date
regular_day = regular_merged[
    (regular_merged["Hospital"] == selected_hospital) &
    (regular_merged["Date"] == pd.to_datetime(selected_date))
]

if regular_day.empty:
    # If no submissions on selected date, calculate 7-day average
    end_date = pd.to_datetime(selected_date)
    start_date = end_date - pd.Timedelta(days=7)

    # Filter last 7 days **with submissions**
    last_7_days = regular_merged[
        (regular_merged["Hospital"] == selected_hospital) &
        (regular_merged["Date"] >= start_date) &
        (regular_merged["Date"] < end_date)
    ]

# --- Single Hospital Function ---
def total_lunch_metric(merged_df, hospital, selected_date):
    """
    Returns total Lunch for selected hospital and date.
    If no submission on selected date, returns 7-day average of past submissions
    and a note that it is an average.
    """
    selected_date = pd.to_datetime(selected_date)
    
    if hospital == "All Hospitals":
        df_hosp = merged_df.copy()
    else:
        df_hosp = merged_df[merged_df["Hospital"] == hospital]
    
    df_day = df_hosp[df_hosp["Date"] == selected_date]
    
    if not df_day.empty:
        total_lunch = df_day["Lunch"].sum()
        note = f"Total Lunch for {selected_date.date()}"
    else:
        end_date = selected_date - pd.Timedelta(days=1)
        start_date = selected_date - pd.Timedelta(days=7)
        last_7_days = df_hosp[
            (df_hosp["Date"] >= start_date) &
            (df_hosp["Date"] <= end_date)
        ]
        if not last_7_days.empty:
            daily_sums = last_7_days.groupby("Date")["Lunch"].sum()
            total_lunch = daily_sums.mean()
            note = f"No submission on {selected_date.date()}. Returning 7-day average based on past submissions."
        else:
            total_lunch = 0
            note = f"No submission on {selected_date.date()} and no data in last 7 days."
    
    return total_lunch, note

# --- all Hospitals Function ---
def total_lunch_all_hospitals(merged_df, selected_date):
    selected_date = pd.to_datetime(selected_date)
    total_lunch = 0
    no_submission_hospitals = []

    hospitals = merged_df["Hospital"].dropna().unique()
    
    for hosp in hospitals:
        df_hosp = merged_df[merged_df["Hospital"] == hosp]
        df_day = df_hosp[df_hosp["Date"] == selected_date]
        
        if not df_day.empty:
            lunch = df_day["Lunch"].sum()
        else:
            end_date = selected_date - pd.Timedelta(days=1)
            start_date = selected_date - pd.Timedelta(days=7)
            last_7_days = df_hosp[
                (df_hosp["Date"] >= start_date) &
                (df_hosp["Date"] <= end_date)
            ]
            if not last_7_days.empty:
                daily_sums = last_7_days.groupby("Date")["Lunch"].sum()
                lunch = daily_sums.mean()
                no_submission_hospitals.append(hosp)
            else:
                lunch = 0
                no_submission_hospitals.append(hosp)
        
        total_lunch += lunch

    if no_submission_hospitals:
        caption_text = "No submission on selected day for: " + ", ".join(no_submission_hospitals)
    else:
        caption_text = f"All hospitals had submissions on {selected_date.date()}"
    
    return total_lunch, caption_text

# --- Usage ---
if selected_hospital == "All Hospitals":
    total_lunch_value, note_text = total_lunch_all_hospitals(regular_merged, selected_date)
else:
    total_lunch_value, note_text = total_lunch_metric(regular_merged, selected_hospital, selected_date)

st.metric("Regular Diet", round(total_lunch_value))
st.caption(note_text)

def post_partum_lunch_metric_hospital(special_df, selected_date, selected_hospital):
    """
    Returns total Lunch for Post-Partum care diet respecting hospital slicer.
    If no submission on that date for a hospital, returns 7-day average.
    For 'All Hospitals', sums across hospitals and lists hospitals with no submission in caption.
    """
    selected_date = pd.to_datetime(selected_date)
    
    # --- Clean data ---
    df = special_df.copy()
    df["Diet"] = df["Diet"].astype(str).str.strip()
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Lunch"] = pd.to_numeric(df["Lunch"], errors="coerce").fillna(0)
    
    # Filter for Post-Partum care diet
    df_diet = df[df["Diet"] == "Post-Partum care diet"]
    
    if selected_hospital == "All Hospitals":
        total_lunch = 0
        no_submission_hospitals = []
        hospitals = df_diet["Hospital"].dropna().unique()
        
        for hosp in hospitals:
            df_h = df_diet[df_diet["Hospital"] == hosp]
            df_day = df_h[df_h["Date"] == selected_date]
            
            if not df_day.empty:
                lunch = df_day["Lunch"].sum()
            else:
                # 7-day average
                start_date = selected_date - pd.Timedelta(days=7)
                end_date = selected_date - pd.Timedelta(days=1)
                last_7_days = df_h[(df_h["Date"] >= start_date) & (df_h["Date"] <= end_date)]
                
                if not last_7_days.empty:
                    daily_sums = last_7_days.groupby("Date")["Lunch"].sum()
                    lunch = daily_sums.mean()
                    no_submission_hospitals.append(hosp)
                else:
                    lunch = 0
                    no_submission_hospitals.append(hosp)
            
            total_lunch += lunch
        
        if no_submission_hospitals:
            note = "No submission on selected day for: " + ", ".join(no_submission_hospitals)
        else:
            note = f"All hospitals had submissions on {selected_date.date()}"
    
    else:
        # Single hospital
        df_h = df_diet[df_diet["Hospital"] == selected_hospital]
        df_day = df_h[df_h["Date"] == selected_date]
        
        if not df_day.empty:
            total_lunch = df_day["Lunch"].sum()
            note = f"Total Post Partum Lunch for {selected_hospital} on {selected_date.date()}"
        else:
            # 7-day average
            start_date = selected_date - pd.Timedelta(days=7)
            end_date = selected_date - pd.Timedelta(days=1)
            last_7_days = df_h[(df_h["Date"] >= start_date) & (df_h["Date"] <= end_date)]
            
            if not last_7_days.empty:
                daily_sums = last_7_days.groupby("Date")["Lunch"].sum()
                total_lunch = daily_sums.mean()
                note = f"No submission on {selected_date.date()} for {selected_hospital}. Returning 7-day average."
            else:
                total_lunch = 0
                note = f"No submission on {selected_date.date()} and no data in last 7 days for {selected_hospital}."
    
    return total_lunch, note
# --- Usage ---
lunch_value, note_text = post_partum_lunch_metric_hospital(
    special_merged, selected_date, selected_hospital
)

st.metric("Total Post-Partum care diet", round(lunch_value))
st.caption(note_text)

def pediatric_diet_care_metric (special_df, selected_date, selected_hospital):
    """
    Returns total Lunch for Pediatric care diet respecting hospital slicer.
    If no submission on that date for a hospital, returns 7-day average.
    For 'All Hospitals', sums across hospitals and lists hospitals with no submission in caption.
    """
    selected_date = pd.to_datetime(selected_date)
    
    # --- Clean data ---
    df = special_df.copy()
    df["Diet"] = df["Diet"].astype(str).str.strip()
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Lunch"] = pd.to_numeric(df["Lunch"], errors="coerce").fillna(0)
    
    # Filter for Pediatric care diet
    df_diet = df[df["Diet"] == "Pediatric care diet"]
    
    if selected_hospital == "All Hospitals":
        total_lunch = 0
        no_submission_hospitals = []
        hospitals = df_diet["Hospital"].dropna().unique()
        
        for hosp in hospitals:
            df_h = df_diet[df_diet["Hospital"] == hosp]
            df_day = df_h[df_h["Date"] == selected_date]
            
            if not df_day.empty:
                lunch = df_day["Lunch"].sum()
            else:
                # 7-day average
                start_date = selected_date - pd.Timedelta(days=7)
                end_date = selected_date - pd.Timedelta(days=1)
                last_7_days = df_h[(df_h["Date"] >= start_date) & (df_h["Date"] <= end_date)]
                
                if not last_7_days.empty:
                    daily_sums = last_7_days.groupby("Date")["Lunch"].sum()
                    lunch = daily_sums.mean()
                    no_submission_hospitals.append(hosp)
                else:
                    lunch = 0
                    no_submission_hospitals.append(hosp)
            
            total_lunch += lunch
        
        if no_submission_hospitals:
            note = "No submission on selected day for: " + ", ".join(no_submission_hospitals)
        else:
            note = f"All hospitals had submissions on {selected_date.date()}"
    
    else:
        # Single hospital
        df_h = df_diet[df_diet["Hospital"] == selected_hospital]
        df_day = df_h[df_h["Date"] == selected_date]
        
        if not df_day.empty:
            total_lunch = df_day["Lunch"].sum()
            note = f"Total Pediatric care diet for {selected_hospital} on {selected_date.date()}"
        else:
            # 7-day average
            start_date = selected_date - pd.Timedelta(days=7)
            end_date = selected_date - pd.Timedelta(days=1)
            last_7_days = df_h[(df_h["Date"] >= start_date) & (df_h["Date"] <= end_date)]
            
            if not last_7_days.empty:
                daily_sums = last_7_days.groupby("Date")["Lunch"].sum()
                total_lunch = daily_sums.mean()
                note = f"No submission on {selected_date.date()} for {selected_hospital}. Returning 7-day average."
            else:
                total_lunch = 0
                note = f"No submission on {selected_date.date()} and no data in last 7 days for {selected_hospital}."
    
    return total_lunch, note

lunch_value, note_text = pediatric_diet_care_metric(
    special_merged, selected_date, selected_hospital
)
st.metric("Total Pediatric care diet", round(lunch_value))
st.caption(note_text)

def easy_digest_care_diet_metric(special_df, selected_date, selected_hospital):

    selected_date = pd.to_datetime(selected_date)

    # --- Clean data ---
    df = special_df.copy()
    df["Diet"] = df["Diet"].astype(str).str.strip()
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Lunch"] = pd.to_numeric(df["Lunch"], errors="coerce").fillna(0)

    # Filter for Easy digest care diet
    df_diet = df[df["Diet"] == "Easy digest care diet"]

    if selected_hospital == "All Hospitals":

        total_lunch = 0
        no_submission_hospitals = []
        hospitals = df_diet["Hospital"].dropna().unique()

        for hosp in hospitals:

            df_h = df_diet[df_diet["Hospital"] == hosp]
            df_day = df_h[df_h["Date"] == selected_date]

            if not df_day.empty:
                lunch = df_day["Lunch"].sum()
            else:
                start_date = selected_date - pd.Timedelta(days=7)
                end_date = selected_date - pd.Timedelta(days=1)

                last_7_days = df_h[
                    (df_h["Date"] >= start_date) &
                    (df_h["Date"] <= end_date)
                ]

                if not last_7_days.empty:
                    daily_sums = last_7_days.groupby("Date")["Lunch"].sum()
                    lunch = daily_sums.mean()
                    no_submission_hospitals.append(hosp)
                else:
                    lunch = 0
                    no_submission_hospitals.append(hosp)

            total_lunch += lunch

        if no_submission_hospitals:
            note = "No submission on selected day for: " + ", ".join(no_submission_hospitals)
        else:
            note = f"All hospitals had submissions on {selected_date.date()}"

    else:
        # ✅ FIXED SINGLE HOSPITAL LOGIC
        df_h = df_diet[df_diet["Hospital"] == selected_hospital]
        df_day = df_h[df_h["Date"] == selected_date]

        if not df_day.empty:
            total_lunch = df_day["Lunch"].sum()
            note = f"Total Easy digest care diet lunch for {selected_hospital} on {selected_date.date()}"
        else:
            start_date = selected_date - pd.Timedelta(days=7)
            end_date = selected_date - pd.Timedelta(days=1)

            last_7_days = df_h[
                (df_h["Date"] >= start_date) &
                (df_h["Date"] <= end_date)
            ]

            if not last_7_days.empty:
                daily_sums = last_7_days.groupby("Date")["Lunch"].sum()
                total_lunch = daily_sums.mean()
                note = f"No submission on {selected_date.date()} for {selected_hospital}. Returning 7-day average."
            else:
                total_lunch = 0
                note = "No submission and no data in last 7 days."

    return total_lunch, note

lunch_value, note_text = easy_digest_care_diet_metric(
    special_merged, selected_date, selected_hospital
)
st.metric("Total Easy digest care diet", round(lunch_value))
st.caption(note_text)

def high_energy_protein_care_diet_metric(special_df, selected_date, selected_hospital):
    selected_date = pd.to_datetime(selected_date)

    # --- Clean data ---
    df = special_df.copy()
    df["Diet"] = df["Diet"].astype(str).str.strip()
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Lunch"] = pd.to_numeric(df["Lunch"], errors="coerce").fillna(0)

    # Filter for High energy/protein care diet
    df_diet = df[df["Diet"] == "High energy/protein care diet"]

    if selected_hospital == "All Hospitals":

        total_lunch = 0
        no_submission_hospitals = []
        hospitals = df_diet["Hospital"].dropna().unique()

        for hosp in hospitals:

            df_h = df_diet[df_diet["Hospital"] == hosp]
            df_day = df_h[df_h["Date"] == selected_date]

            if not df_day.empty:
                lunch = df_day["Lunch"].sum()
            else:
                start_date = selected_date - pd.Timedelta(days=7)
                end_date = selected_date - pd.Timedelta(days=1)

                last_7_days = df_h[
                    (df_h["Date"] >= start_date) &
                    (df_h["Date"] <= end_date)
                ]

                if not last_7_days.empty:
                    daily_sums = last_7_days.groupby("Date")["Lunch"].sum()
                    lunch = daily_sums.mean()
                    no_submission_hospitals.append(hosp)
                else:
                    lunch = 0
                    no_submission_hospitals.append(hosp)

            total_lunch += lunch

        if no_submission_hospitals:
            note = "No submission on selected day for: " + ", ".join(no_submission_hospitals)
        else:
            note = f"All hospitals had submissions on {selected_date.date()}"

    else:
        # ✅ FIXED SINGLE HOSPITAL LOGIC
        df_h = df_diet[df_diet["Hospital"] == selected_hospital]
        df_day = df_h[df_h["Date"] == selected_date]

        if not df_day.empty:
            total_lunch = df_day["Lunch"].sum()
            note = f"Total High energy/protein care diet lunch for {selected_hospital} on {selected_date.date()}"
        else:
            start_date = selected_date - pd.Timedelta(days=7)
            end_date = selected_date - pd.Timedelta(days=1)

            last_7_days = df_h[
                (df_h["Date"] >= start_date) &
                (df_h["Date"] <= end_date)
            ]
            if not last_7_days.empty:
                daily_sums = last_7_days.groupby("Date")["Lunch"].sum()
                total_lunch = daily_sums.mean()
                note = f"No submission on {selected_date.date()} for {selected_hospital}. Returning 7-day average."
            else:
                total_lunch = 0
                note = "No submission and no data in last 7 days."
    return total_lunch, note

lunch_value, note_text = high_energy_protein_care_diet_metric(
    special_merged, selected_date, selected_hospital
)
st.metric("Total High energy/protein care diet", round(lunch_value))    
st.caption(note_text)

def diabetic_care_diet_metric(special_df, selected_date, selected_hospital):
    selected_date = pd.to_datetime(selected_date)

    # --- Clean data ---
    df = special_df.copy()
    df["Diet"] = df["Diet"].astype(str).str.strip()
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Lunch"] = pd.to_numeric(df["Lunch"], errors="coerce").fillna(0)

    # Filter for Diabetic care diet
    df_diet = df[df["Diet"] == "Diabetic care diet"]

    if selected_hospital == "All Hospitals":

        total_lunch = 0
        no_submission_hospitals = []
        hospitals = df_diet["Hospital"].dropna().unique()

        for hosp in hospitals:

            df_h = df_diet[df_diet["Hospital"] == hosp]
            df_day = df_h[df_h["Date"] == selected_date]

            if not df_day.empty:
                lunch = df_day["Lunch"].sum()
            else:
                start_date = selected_date - pd.Timedelta(days=7)
                end_date = selected_date - pd.Timedelta(days=1)

                last_7_days = df_h[
                    (df_h["Date"] >= start_date) &
                    (df_h["Date"] <= end_date)
                ]

                if not last_7_days.empty:
                    daily_sums = last_7_days.groupby("Date")["Lunch"].sum()
                    lunch = daily_sums.mean()
                    no_submission_hospitals.append(hosp)
                else:
                    lunch = 0
                    no_submission_hospitals.append(hosp)

            total_lunch += lunch

        if no_submission_hospitals:
            note = "No submission on selected day for: " + ", ".join(no_submission_hospitals)
        else:
            note = f"All hospitals had submissions on {selected_date.date()}"

    else:
        # ✅ FIXED SINGLE HOSPITAL LOGIC
        df_h = df_diet[df_diet["Hospital"] == selected_hospital]
        df_day = df_h[df_h["Date"] == selected_date]

        if not df_day.empty:
            total_lunch = df_day["Lunch"].sum()
            note = f"Total Diabetic care diet lunch for {selected_hospital} on {selected_date.date()}"
        else:
            start_date = selected_date - pd.Timedelta(days=7)
            end_date = selected_date - pd.Timedelta(days=1)

            last_7_days = df_h[
                (df_h["Date"] >= start_date) &
                (df_h["Date"] <= end_date)
            ]
            if not last_7_days.empty:
                daily_sums = last_7_days.groupby("Date")["Lunch"].sum()
                total_lunch = daily_sums.mean()
                note = f"No submission on {selected_date.date()} for {selected_hospital}. Returning 7-day average."
            else:
                total_lunch = 0
                note = "No submission and no data in last 7 days."

    return total_lunch, note
lunch_value, note_text = diabetic_care_diet_metric(
    special_merged, selected_date, selected_hospital
)
st.metric("Total Diabetic care diet", round(lunch_value))
st.caption(note_text)

def sodium_restricted_care_diet_metric(special_df, selected_date, selected_hospital):
    df = special_df.copy()
    df["Diet"] = df["Diet"].astype(str).str.strip()
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Lunch"] = pd.to_numeric(df["Lunch"], errors="coerce").fillna(0)

# Filter for Sodium restricted/No salt diet
    df_diet = df[df["Diet"] == "Sodium restricted/No salt diet"]
    
    if selected_hospital == "All Hospitals":

        total_lunch = 0
        no_submission_hospitals = []
        hospitals = df_diet["Hospital"].dropna().unique()

        for hosp in hospitals:

            df_h = df_diet[df_diet["Hospital"] == hosp]
            df_day = df_h[df_h["Date"] == selected_date]

            if not df_day.empty:
                lunch = df_day["Lunch"].sum()
            else:
                start_date = selected_date - pd.Timedelta(days=7)
                end_date = selected_date - pd.Timedelta(days=1)

                last_7_days = df_h[
                    (df_h["Date"] >= start_date) &
                    (df_h["Date"] <= end_date)
                ]

                if not last_7_days.empty:
                    daily_sums = last_7_days.groupby("Date")["Lunch"].sum()
                    lunch = daily_sums.mean()
                    no_submission_hospitals.append(hosp)
                else:
                    lunch = 0
                    no_submission_hospitals.append(hosp)

            total_lunch += lunch

        if no_submission_hospitals:
            note = "No submission on selected day for: " + ", ".join(no_submission_hospitals)
        else:
            note = f"All hospitals had submissions on {selected_date.date()}"
    else:
        #single hospital
        df_h = df_diet[df_diet["Hospital"] == selected_hospital]
        df_day = df_h[df_h["Date"] == selected_date]

        if not df_day.empty:
            total_lunch = df_day["Lunch"].sum()
            note = f"Total Sodium restricted/No salt diet lunch for {selected_hospital} on {selected_date.date()}"
        else:
            start_date = selected_date - pd.Timedelta(days=7)
            end_date = selected_date - pd.Timedelta(days=1)

            last_7_days = df_h[
                (df_h["Date"] >= start_date) &
                (df_h["Date"] <= end_date)
            ]
            if not last_7_days.empty:
                daily_sums = last_7_days.groupby("Date")["Lunch"].sum()
                total_lunch = daily_sums.mean()
                note = f"No submission on {selected_date.date()} for {selected_hospital} Hospital. Returning 7-day average."
            else:
                total_lunch = 0
                note = f"No submission and no data in last 7 days for {selected_hospital} Hospital."

    return total_lunch, note

lunch_value, note_text = sodium_restricted_care_diet_metric(
        special_merged, selected_date, selected_hospital
)
st.metric("Total Sodium restricted/No salt diet", round(lunch_value))
st.caption(note_text)

def izere_pavillion_other_private_inpatient_diet_metric(special_df, selected_date, selected_hospital):
    df = special_df.copy()
    df["Diet"] = df["Diet"].astype(str).str.strip()
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Lunch"] = pd.to_numeric(df["Lunch"], errors="coerce").fillna(0)

    # Filter for IZERE/Pavillion/Other Private inpatient diets
    df_diet = df[df["Diet"] == "IZERE/Pavillion/Other Private inpatient diets"]

    if selected_hospital == "All Hospitals":

        total_lunch = 0
        no_submission_hospitals = []
        hospitals = df_diet["Hospital"].dropna().unique()

        for hosp in hospitals:
            df_h = df_diet[df_diet["Hospital"] == hosp]
            df_day = df_h[df_h["Date"] == selected_date]

            if not df_day.empty:
                lunch = df_day["Lunch"].sum()
            else:
                start_date = selected_date - pd.Timedelta(days=7)
                end_date = selected_date - pd.Timedelta(days=1)

                last_7_days = df_h[
                    (df_h["Date"] >= start_date) &
                    (df_h["Date"] <= end_date)
                ]

                if not last_7_days.empty:
                    daily_sums = last_7_days.groupby("Date")["Lunch"].sum()
                    lunch = daily_sums.mean()
                    no_submission_hospitals.append(hosp)
                else:
                    lunch = 0
                    no_submission_hospitals.append(hosp)

            total_lunch += lunch
        
        if no_submission_hospitals:
            note = "No submission on selected day for: " + ", ".join(no_submission_hospitals)
        else:
            note = f"All hospitals had submissions on {selected_date.date()}"
    else:
        # Single hospital
        df_h = df_diet[df_diet["Hospital"] == selected_hospital]
        df_day = df_h[df_h["Date"] == selected_date]

        if not df_day.empty:
            total_lunch = df_day["Lunch"].sum()
            note = f"Total IZERE/Pavillion/Other Private inpatient diet lunch for {selected_hospital} on {selected_date.date()}"
        else:
            start_date = selected_date - pd.Timedelta(days=7)
            end_date = selected_date - pd.Timedelta(days=1)

            last_7_days = df_h[
                (df_h["Date"] >= start_date) &
                (df_h["Date"] <= end_date)
            ]

            if not last_7_days.empty:
                daily_sums = last_7_days.groupby("Date")["Lunch"].sum()
                total_lunch = daily_sums.mean()
                note = f"No submission on {selected_date.date()} for {selected_hospital}. Returning 7-day average."
            else:
                total_lunch = 0
                note = f"No submission and no data in last 7 days for {selected_hospital} Hospital."
    return total_lunch, note
lunch_value, note_text = izere_pavillion_other_private_inpatient_diet_metric(
    special_merged, selected_date, selected_hospital
)
st.metric("Total IZERE/Pavillion/Other Private inpatient diets", round(lunch_value))
st.caption(note_text)

def calculate_lunch(df, selected_date, selected_hospital, diet_name=None):
    """
    Returns total Lunch for a diet dataframe, respecting hospital and date.
    If diet_name is given, filters by that diet.
    Uses 7-day average if no submission.
    Works for single or all hospitals.
    """
    selected_date = pd.to_datetime(selected_date)
    df_clean = df.copy()
    
    # Clean columns
    df_clean["Date"] = pd.to_datetime(df_clean["Date"], errors="coerce")
    df_clean["Lunch"] = pd.to_numeric(df_clean["Lunch"], errors="coerce").fillna(0)
    df_clean["Hospital"] = df_clean["Hospital"].astype(str).str.strip()
    if diet_name:
        df_clean = df_clean[df_clean["Diet"].astype(str).str.strip() == diet_name]

    # Default values
    total_lunch = 0
    note = ""
    
    if selected_hospital == "All Hospitals":
        hospitals = df_clean["Hospital"].dropna().unique()
        no_submission_hospitals = []
        
        for hosp in hospitals:
            df_h = df_clean[df_clean["Hospital"] == hosp]
            df_day = df_h[df_h["Date"] == selected_date]
            
            if not df_day.empty:
                lunch = df_day["Lunch"].sum()
            else:
                # 7-day average
                start_date = selected_date - pd.Timedelta(days=7)
                end_date = selected_date - pd.Timedelta(days=1)
                last_7_days = df_h[(df_h["Date"] >= start_date) & (df_h["Date"] <= end_date)]
                
                if not last_7_days.empty:
                    lunch = last_7_days.groupby("Date")["Lunch"].sum().mean()
                    no_submission_hospitals.append(hosp)
                else:
                    lunch = 0
                    no_submission_hospitals.append(hosp)
            
            total_lunch += lunch
        
        if no_submission_hospitals:
            note = "No submission on selected day for: " + ", ".join(no_submission_hospitals)
    else:
        # Single hospital
        df_h = df_clean[df_clean["Hospital"] == selected_hospital]
        df_day = df_h[df_h["Date"] == selected_date]
        if not df_day.empty:
            total_lunch = df_day["Lunch"].sum()
        else:
            start_date = selected_date - pd.Timedelta(days=7)
            end_date = selected_date - pd.Timedelta(days=1)
            last_7_days = df_h[(df_h["Date"] >= start_date) & (df_h["Date"] <= end_date)]
            if not last_7_days.empty:
                total_lunch = last_7_days.groupby("Date")["Lunch"].sum().mean()
            else:
                total_lunch = 0
        # note remains "" if no missing submissions
    
    return total_lunch, note

# ---------------------------
# Calculate totals for all diets
# ---------------------------
regular_total, regular_note = calculate_lunch(regular_merged, selected_date, selected_hospital)
postpartum_total, pp_note = calculate_lunch(special_merged, selected_date, selected_hospital, "Post-Partum care diet")
pediatric_total, ped_note = calculate_lunch(special_merged, selected_date, selected_hospital, "Pediatric care diet")
easy_digest_total, ed_note = calculate_lunch(special_merged, selected_date, selected_hospital, "Easy digest care diet")
sodium_total, sr_note = calculate_lunch(special_merged, selected_date, selected_hospital, "Sodium restricted/No salt diet")
high_energy_total, he_note = calculate_lunch(special_merged, selected_date, selected_hospital, "High energy/protein care diet")
diabetic_total, dia_note = calculate_lunch(special_merged, selected_date, selected_hospital, "Diabetic care diet")
izere_total, izere_note = calculate_lunch(special_merged, selected_date, selected_hospital, "IZERE/Pavillion/Other Private inpatient diets")

# Total meals across all diets
total_meals = regular_total + postpartum_total + pediatric_total + easy_digest_total + sodium_total + high_energy_total + diabetic_total + izere_total

# Combine all notes
notes = [note for note in [regular_note, pp_note, ped_note, ed_note, sr_note, he_note, dia_note, izere_note] if note]
total_note = "; ".join(notes) if notes else ""

# ---------------------------
# Display in Streamlit box
# ---------------------------
with st.container():
    st.markdown(f"""
        <div style="
            border: 0px solid #ffffff; 
            padding: 1px;
            border-radius: 5px; 
            background-color: #c91530; 
            width: 220px; 
            display: flex; 
            flex-direction: column; 
            align-items: center; 
            justify-content: center;
        ">
            <p style="color: #ffffff; margin: 0px 0 0 0; font-size: 22px; padding-bottom: 0px; padding-top: 10px; line-height: 1;">Total Meals Served</p>
            <p style="color: #ffffff; margin: 0px 0 0 0; font-size: 50px; font-weight: bold; padding-bottom: 15px; padding-top: 5px;line-height: 1;">{round(total_meals)}</p>
        </div>
    """, unsafe_allow_html=True)


# Clean Challenge_satisfaction column: remove line breaks
regular_merged["Challenge_satisfaction"] = (
    regular_merged["Challenge_satisfaction"]
    .astype(str)                     # ensure it's string
    .str.replace(r'[\r\n]+', ' ', regex=True)  # replace line breaks with a space
    .str.strip()                     # remove leading/trailing spaces
)

# Filter data for selected date
df_comments = regular_merged[regular_merged["Date"] == pd.to_datetime(selected_date)]

# If a specific hospital is selected, filter
if selected_hospital != "All Hospitals":
    df_comments = df_comments[df_comments["Hospital"] == selected_hospital]

# Only keep rows with comments
df_comments = df_comments[df_comments["Challenge_satisfaction"].notna()]

# Define colors for hospitals
hospital_colors = {
    "CHUK": "#FF6F61",
    "KIBAGABAGA": "#6B5B95",
    "MASAKA": "#88B04B",
    "MUHIMA": "#6F087F",
    "NYARUGENGE": "#4D7BD1"
}

# Display comments
if not df_comments.empty:
    st.markdown("### Comments and Recommendations")
    
    for idx, row in df_comments.iterrows():
        hosp = row["Hospital"]
        comment = row["Challenge_satisfaction"]
        color = hospital_colors.get(hosp, "#000000")  # default black if hospital not in dict

        st.markdown(
            f'<p style="color:{color}; font-weight:500;">'
            f'<b>{hosp}:</b> {comment}'
            f'</p>',
            unsafe_allow_html=True
        )
else:
    st.info("No comments available for the selected date/hospital.")
    