# 2025-02-19-upwork-clintrials-streamlit-v1.3

# v 1.1 
#Great! To create a simple, interactive dashboard (an MVP) we can build a small web app that:
#	1.	Loads and parses the JSON data from our SQLite DB.
#We’ll extract key fields such as:
#	•	studyFirstSubmitDate (from protocolSection.statusModule.studyFirstSubmitDate)
#	•	Lead Sponsor Name & Class (from protocolSection.sponsorCollaboratorsModule.leadSponsor)
#	•	Conditions (from protocolSection.conditionsModule.conditions)
#	•	Study Type (from protocolSection.designModule.studyType)
#	•	Intervention Names (from the armsInterventionsModule – e.g., from each armGroup’s interventionNames)
#	•	Phases (from protocolSection.designModule.phases)
#	•	Facilities and their Locations (from protocolSection.contactsLocationsModule.locations; note that there might be multiple facilities per study so we can aggregate them into a comma‐separated string that also shows city, state, and country)
#	•	Status (from protocolSection.statusModule.overallStatus)
#	2.	Build an interactive dashboard using Streamlit.
#Streamlit is ideal for quickly creating filtering widgets (e.g., dropdowns, multiselects) and generating charts (bar charts, pie charts) and a data table that updates as you adjust the filters.
#	3.	Design the Report Layout.
#	•	Sidebar Filters: For example, a filter for “Trial Phase” (e.g., Phase 2), “Study Type,” or “Status.”
#	•	Main Panel:
#	•	At the top, display a few charts (e.g., a bar chart of studies by country, a pie chart by phase, etc.).
#	•	Below the charts, display a table of the filtered studies.


#v 1 .2

# Below is an updated app.py example that:
#	1.	Moves the full studies table to the bottom of the page.
#	2.	Adds horizontal bar charts for:
#	•	Top 20 Trial Sites (by facility name)
#	•	Top 20 Countries
#	•	Top 20 Primary Interventions
#	3.	Parses “modality” from each intervention name (e.g., "Drug: Pembrolizumab" → "Drug") and includes a bar chart for modalities.

#How This Works
#	1.	Data Loading & Extraction:
#	•	We load studies from UW_clin_trials.db, parse each JSON, and create a Pandas DataFrame with key columns (studyFirstSubmitDate, leadSponsorName, interventionNames, etc.).
#	2.	Additional Parsing Columns:
#	•	sites_list: Splits the semicolon‐delimited facility string into multiple site names (one study can have many sites).
#	•	countries_list: Extracts the country from each site’s (city, state, country) block.
#	•	primary_intervention: Grabs just the first intervention name if there are multiple.
#	•	modalities_list: Splits each intervention name (e.g., "Drug: Pembrolizumab") to capture "Drug", "Device", "Biological", etc.
#	3.	Filtering:
#	•	We filter on Phase, Study Type, and Overall Status. The df_filtered result is used for charts and the final table.
#	4.	Charts:
#	•	Horizontal Bar Charts (using Altair) for:
#	•	Top 20 Trial Sites by frequency
#	•	Top 20 Countries by frequency
#	•	Top 20 Primary Interventions
#	•	All Modalities (counts each modality, so if a study has multiple modalities, it will appear multiple times)
#	5.	Table at the Bottom:
#	•	After the charts, we display the filtered DataFrame so users can see details for each trial.

# v 1.3
#What’s New?
#	1.	interventionNamesNoModalityList:
#A new function parse_intervention_names_no_modality() returns a list of intervention names after the colon while excluding any items whose modality is "Behavioral" or "Procedure".
#	2.	Top 20 Intervention Names (No Modality):
#We explode that new list column and create a horizontal bar chart for the top 20.
#	3.	Top 20 Lead Sponsors:
#We added a bar chart summarizing the top 20 most common lead sponsors.
#	4.	Existing Charts:
#	•	Top 20 Trial Sites
#	•	Top 20 Countries
#	•	Top 20 Primary Interventions (the first item in the interventionNames string)
#	•	Trials by Modality

# v 1 .4

#Below is an updated app.py example that:
#	1.	Adds a summary at the very top indicating how many new clinical trials were posted in the last 7 days.
#	2.	Reorders the charts so that:
#	•	First Chart: A vertical bar chart showing the number of trials by phase.
#	•	Second Chart: A stacked vertical bar chart with phase on the X-axis and modality as the color stacks.
#	3.	Keeps the remaining charts (sites, countries, interventions, etc.) and the final table at the bottom.


# v 1 . 5 
# bug fix as graphs were not showing due to phase filtering

import streamlit as st
import sqlite3
import pandas as pd
import json
import altair as alt
from datetime import datetime, timedelta

# -------------- Helper Functions --------------

# Get today's date
today = datetime.today()
start_date = today - timedelta(days=7)  # Last 7 days

# Format the dates as "Month Day, Year" (e.g., "February 12, 2025")
start_date_str = start_date.strftime('%B %d, %Y')
end_date_str = today.strftime('%B %d, %Y')

def extract_study_data(study):
    """Extract key fields from a study JSON into a dict."""
    ps = study.get("protocolSection", {})
    
    # statusModule fields
    status_module = ps.get("statusModule", {})
    study_first_submit = status_module.get("studyFirstSubmitDate", None)
    overall_status = status_module.get("overallStatus", None)
    
    # sponsorCollaboratorsModule: leadSponsor
    sponsor_module = ps.get("sponsorCollaboratorsModule", {})
    lead_sponsor = sponsor_module.get("leadSponsor", {})
    lead_sponsor_name = lead_sponsor.get("name", None)
    lead_sponsor_class = lead_sponsor.get("class", None)
    
    # conditionsModule: conditions
    conditions_module = ps.get("conditionsModule", {})
    conditions = conditions_module.get("conditions", [])
    conditions_str = ", ".join(conditions) if conditions else None
    
    # designModule: studyType and phases
    design_module = ps.get("designModule", {})
    study_type = design_module.get("studyType", None)
    phases = design_module.get("phases", [])
    phases_str = ", ".join(phases) if phases else None
    
    # armsInterventionsModule: interventionNames
    arms_module = ps.get("armsInterventionsModule", {})
    arm_groups = arms_module.get("armGroups", [])
    interventions = set()
    for group in arm_groups:
        names = group.get("interventionNames", [])
        for name in names:
            interventions.add(name)
    intervention_names_str = ", ".join(sorted(interventions)) if interventions else None
    
    # contactsLocationsModule: locations (facility + city, state, country)
    contacts_module = ps.get("contactsLocationsModule", {})
    locations = contacts_module.get("locations", [])
    facilities = []
    for loc in locations:
        facility = loc.get("facility", "")
        city = loc.get("city", "")
        state = loc.get("state", "")
        country = loc.get("country", "")
        loc_info = f"{facility} ({city}, {state}, {country})".strip()
        facilities.append(loc_info)
    facilities_str = "; ".join(facilities) if facilities else None
    
    return {
        "studyFirstSubmitDate": study_first_submit,
        "leadSponsorName": lead_sponsor_name,
        "leadSponsorClass": lead_sponsor_class,
        "conditions": conditions_str,
        "studyType": study_type,
        "interventionNames": intervention_names_str,
        "phases": phases_str,
        "facilities": facilities_str,
        "overallStatus": overall_status
    }

def load_data_from_db(db_name="data/clinical-trials-api.db"):
    """Load study data from the SQLite DB and return a DataFrame of extracted fields."""
    conn = sqlite3.connect(db_name)
    query = "SELECT nct_id, json_data FROM studies"
    df_raw = pd.read_sql(query, conn)
    conn.close()
    
    records = []
    for _, row in df_raw.iterrows():
        try:
            study_json = json.loads(row["json_data"])
            data = extract_study_data(study_json)
            data["nct_id"] = row["nct_id"]
            records.append(data)
        except Exception as e:
            print(f"Error processing study {row['nct_id']}: {e}")
    return pd.DataFrame(records)

# --- Additional parsing for sites, countries, and interventions ---

def parse_facilities_list(facilities_str):
    """Split the semicolon-delimited facilities into a list of site names."""
    if not facilities_str:
        return []
    items = facilities_str.split("; ")
    site_names = []
    for i in items:
        # Site name is everything before the first "("
        site = i.split("(")[0].strip()
        if site:
            site_names.append(site)
    return site_names

def parse_countries_list(facilities_str):
    """Split the semicolon-delimited facilities and parse out countries."""
    if not facilities_str:
        return []
    items = facilities_str.split("; ")
    countries = []
    for i in items:
        if "(" in i and ")" in i:
            content = i.split("(")[-1].split(")")[0]
            parts = [p.strip() for p in content.split(",")]
            if len(parts) == 3:
                countries.append(parts[2])
    return countries

def parse_modalities_list(interventions_str):
    """
    Extract the 'modality' from each intervention name.
    e.g., 'Drug: Pembrolizumab' => 'Drug'
    If no colon found, label as 'Unknown'.
    """
    if not interventions_str:
        return []
    items = [x.strip() for x in interventions_str.split(",")]
    modalities = []
    for i in items:
        if ":" in i:
            modality = i.split(":", 1)[0].strip()
            modalities.append(modality)
        else:
            modalities.append("Unknown")
    return modalities

def parse_primary_intervention(interventions_str):
    """Return the first listed intervention (if multiple)."""
    if not interventions_str:
        return None
    items = [x.strip() for x in interventions_str.split(",")]
    return items[0] if items else None

def parse_intervention_names_no_modality(interventions_str):
    """
    Return a list of intervention names *excluding* those with modality 'Behavioral' or 'Procedure'.
    E.g. 'Drug: Pembrolizumab' => 'Pembrolizumab'
    If no colon, treat the entire item as the 'name'.
    """
    if not interventions_str:
        return []
    items = [x.strip() for x in interventions_str.split(",")]
    names_no_modality = []
    for item in items:
        if ":" in item:
            modality, name = item.split(":", 1)
            modality = modality.strip().lower()
            name = name.strip()
            if modality not in ["behavioral", "procedure"]:
                names_no_modality.append(name)
        else:
            if item.lower() not in ["behavioral", "procedure"]:
                names_no_modality.append(item)
    return names_no_modality

def horizontal_bar_chart(df, x_col, y_col, title):
    """Return an Altair horizontal bar chart."""
    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X(x_col, title="Count"),
            y=alt.Y(y_col, sort="-x", title=""),
            tooltip=[y_col, x_col],
        )
        .properties(title=title, width=700, height=400)
    )
    return chart

def vertical_bar_chart(df, x_col, y_col, title):
    """Return an Altair vertical bar chart."""
    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X(x_col, sort=None, title=""),
            y=alt.Y(y_col, title="Count"),
            tooltip=[x_col, y_col],
        )
        .properties(title=title, width=700, height=400)
    )
    return chart

def stacked_vertical_bar_chart(df, x_col, y_col, stack_col, title):
    """Return an Altair stacked vertical bar chart."""
    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X(x_col, sort=None, title=""),
            y=alt.Y(y_col, title="Count"),
            color=alt.Color(stack_col, legend=alt.Legend(title=stack_col)),
            tooltip=[x_col, stack_col, y_col],
        )
        .properties(title=title, width=700, height=400)
    )
    return chart


# -------------- Streamlit App --------------

def main():
    st.title("Clinical Trials Dashboard")
    
    # Load data
    df = load_data_from_db()
    
    # Summary text at the top (assumes all trials are within the last 7 days)
    count_all = len(df)
    st.markdown(f"**{count_all} new clinical trials were posted in the last 7 days ({start_date_str} - {end_date_str}).**")
    
    # Parse out lists for sites, countries, primary intervention, modalities, and phases
    df["sites_list"] = df["facilities"].apply(parse_facilities_list)
    df["countries_list"] = df["facilities"].apply(parse_countries_list)
    df["modalities_list"] = df["interventionNames"].apply(parse_modalities_list)
    df["primary_intervention"] = df["interventionNames"].apply(parse_primary_intervention)
    df["interventionNamesNoModalityList"] = df["interventionNames"].apply(parse_intervention_names_no_modality)
    
    def split_phases(phases_str):
        if not phases_str:
            return []
        return [p.strip() for p in phases_str.split(",")]
    df["phases_list"] = df["phases"].apply(split_phases)
    
    # ---------------- Sidebar Filters ----------------
    st.sidebar.header("Filter Studies")
    
    all_phases = sorted(set(sum((p.split(", ") for p in df["phases"].dropna()), [])))
    selected_phases = st.sidebar.multiselect("Trial Phase", all_phases, default=all_phases)
    
    all_study_types = sorted(df["studyType"].dropna().unique())
    selected_study_types = st.sidebar.multiselect("Study Type", all_study_types, default=all_study_types)
    
    all_statuses = sorted(df["overallStatus"].dropna().unique())
    selected_statuses = st.sidebar.multiselect("Status", all_statuses, default=all_statuses)
    
    def filter_df(df):
        # Use phases_list instead of phases
        mask_phase = df["phases_list"].apply(lambda x: any(phase in selected_phases for phase in x))
        mask_type = df["studyType"].isin(selected_study_types)
        mask_status = df["overallStatus"].isin(selected_statuses)
        return df[mask_phase & mask_type & mask_status]
    
    df_filtered = filter_df(df)
    
    # -------------- Charts Section --------------
    
    # First Chart: Vertical bar chart of number of trials by Phase
    phases_exploded = df_filtered.explode("phases_list")
    phase_counts = phases_exploded["phases_list"].value_counts().reset_index()
    phase_counts.columns = ["phase", "count"]
    
    if not phase_counts.empty:
        chart_phase = vertical_bar_chart(phase_counts, "phase", "count", "Number of Trials by Phase")
        st.altair_chart(chart_phase, use_container_width=True)
    
    # Second Chart: Stacked vertical bar chart with Phase on X and Modality as stacks
    pm_exploded = df_filtered.explode("phases_list").explode("modalities_list")
    pm_exploded = pm_exploded.dropna(subset=["phases_list", "modalities_list"])
    pm_counts = pm_exploded.groupby(["phases_list", "modalities_list"]).size().reset_index(name="count")
    
    if not pm_counts.empty:
        chart_stack = stacked_vertical_bar_chart(
            pm_counts,
            x_col="phases_list",
            y_col="count",
            stack_col="modalities_list",
            title="Trials by Phase (Stacked by Modality)"
        )
        st.altair_chart(chart_stack, use_container_width=True)
    
    # ---------------- Additional Horizontal Charts ----------------
    st.subheader("Additional Charts")
    
    sites_exploded = df_filtered.explode("sites_list")
    site_counts = sites_exploded["sites_list"].value_counts().nlargest(20).reset_index()
    site_counts.columns = ["site_name", "count"]
    if not site_counts.empty:
        chart_sites = horizontal_bar_chart(site_counts, "count", "site_name", "Top 20 Trial Sites by Frequency")
        st.altair_chart(chart_sites, use_container_width=True)
    
    countries_exploded = df_filtered.explode("countries_list")
    country_counts = countries_exploded["countries_list"].value_counts().nlargest(20).reset_index()
    country_counts.columns = ["country", "count"]
    if not country_counts.empty:
        chart_countries = horizontal_bar_chart(country_counts, "count", "country", "Top 20 Countries by Frequency")
        st.altair_chart(chart_countries, use_container_width=True)
    
    pi_counts = df_filtered["primary_intervention"].value_counts().nlargest(20).reset_index()
    pi_counts.columns = ["primary_intervention", "count"]
    if not pi_counts.empty:
        chart_pi = horizontal_bar_chart(pi_counts, "count", "primary_intervention", "Top 20 Primary Interventions (First Listed)")
        st.altair_chart(chart_pi, use_container_width=True)
    
    modalities_exploded = df_filtered.explode("modalities_list")
    modality_counts = modalities_exploded["modalities_list"].value_counts().reset_index()
    modality_counts.columns = ["modality", "count"]
    if not modality_counts.empty:
        chart_modality = horizontal_bar_chart(modality_counts, "count", "modality", "Trials by Modality")
        st.altair_chart(chart_modality, use_container_width=True)
    
    no_mod_exploded = df_filtered.explode("interventionNamesNoModalityList")
    no_mod_counts = no_mod_exploded["interventionNamesNoModalityList"].value_counts().nlargest(20).reset_index()
    no_mod_counts.columns = ["interventionName", "count"]
    if not no_mod_counts.empty:
        chart_no_mod = horizontal_bar_chart(no_mod_counts, "count", "interventionName", "Top 20 Intervention Names (No Modality)")
        st.altair_chart(chart_no_mod, use_container_width=True)
    
    sponsor_counts = df_filtered["leadSponsorName"].value_counts().nlargest(20).reset_index()
    sponsor_counts.columns = ["leadSponsorName", "count"]
    if not sponsor_counts.empty:
        chart_sponsor = horizontal_bar_chart(sponsor_counts, "count", "leadSponsorName", "Top 20 Lead Sponsors")
        st.altair_chart(chart_sponsor, use_container_width=True)
    
    # ---------------- Table Section ----------------
    st.subheader(f"Filtered Studies ({df_filtered.shape[0]} records)")
    st.dataframe(df_filtered)

if __name__ == "__main__":
    main()