import streamlit as st
import pandas as pd
import json
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

st.set_page_config(
    page_title="Results",  
    page_icon="📊",      
)

st.title("Survey Results")
st.write("""My survey is designed to answer the question "How does a person's daily step count affect their energy level?"
Many researchers belive that increased physical activity, especially cardio, will contribute to a hightened energy level.
One study by Clarkson University (Wender et al., 2022) agrees, finding "moderate intensity exercise... [is] on average beneficial for fatigue, energy, and vitality".
Using my survey, I tracked my steps and energy levels for the past 2 weeks to test the correlation between steps and my energy level. 
""")

base_dir = Path(__file__).resolve().parent.parent
csv_path = base_dir / "data.csv"
json_path = base_dir / "data.json"

#Load data.csv
data_path = csv_path
if not data_path.exists() or data_path.stat().st_size == 0:
    for key in list(st.session_state.keys()):
        if key not in ["date_start", "date_end"]:
            del st.session_state[key]

    st.warning("No survey data found yet.")
    st.info("Please go to the **Survey page** and enter your walking and energy data to generate visualizations.")
    st.stop()

else:
    df = pd.read_csv(data_path, parse_dates=["date"])
    df["steps"] = pd.to_numeric(df["steps"], errors="coerce").fillna(0).astype(int)
    df["energy"] = pd.to_numeric(df["energy"], errors="coerce").fillna(0).astype(int)
    df = df.dropna(subset=["date"])
    df = df[(df["steps"] > 0) & (df["energy"] > 0)]


#load data.json
if json_path.exists():
    meta = json.loads(json_path.read_text())
else:
    meta = {}

st.sidebar.header("Filters & Controls")

if df.empty or df["date"].isna().all():
    st.warning("🚶‍♂️ No valid data available yet.")
    st.info("Please complete the survey to see visualizations.")
    st.stop()

min_date = df["date"].min().date()
max_date = df["date"].max().date()

dynamic_max_steps = min(100000, int(df["steps"].max()))

if "date_start" not in st.session_state:
    st.session_state.date_start = min_date
if "date_end" not in st.session_state:
    st.session_state.date_end = max_date
if "min_steps" not in st.session_state:
    st.session_state.min_steps = int(df["steps"].min())
if "max_steps" not in st.session_state:
    st.session_state.max_steps = dynamic_max_steps
if "keyword" not in st.session_state:
    st.session_state.keyword = ""
if "apply_filters" not in st.session_state:
    st.session_state.apply_filters = False

#Sidebar data filtering thing
with st.sidebar.form(key="filter_form"):
    st.subheader("Set Filters")

    st.session_state.date_start = st.date_input(
        "Start Date", value=st.session_state.date_start, min_value=min_date, max_value=max_date
    )
    st.session_state.date_end = st.date_input(
        "End Date", value=st.session_state.date_end, min_value=min_date, max_value=max_date
    )
    st.session_state.min_steps = st.number_input(
        "Minimum Steps",
        min_value=0,
        max_value=100000,
        value=st.session_state.min_steps,
        step=100
    )
    st.session_state.max_steps = st.number_input(
        "Maximum Steps",
        min_value=int(st.session_state.min_steps),
        max_value=100000,
        value=st.session_state.max_steps,
        step=100
    )
    st.session_state.keyword = st.text_input(
        "Keyword in Notes (optional)",
        value=st.session_state.keyword,
        placeholder="e.g. tired, caffeine"
    )
    apply_filters = st.form_submit_button("Apply Filters")

#Apply filters button

if apply_filters:
    st.session_state.apply_filters = True

if st.session_state.apply_filters:
    filtered = df[
        (df["date"].dt.date >= st.session_state.date_start) &
        (df["date"].dt.date <= st.session_state.date_end) &
        (df["steps"] >= st.session_state.min_steps) &
        (df["steps"] <= st.session_state.max_steps)
    ]
    if st.session_state.keyword.strip():
        filtered = filtered[filtered["notes"].str.contains(st.session_state.keyword, case=False, na=False)]
else:
    filtered = df.copy()

#The cited study graph w data from json STATIC GRAPH
st.subheader("Energy improvement in Clarkson University Study")
if meta.get("study_energy_effects"):
    study_data = meta["study_energy_effects"]
    study_df = pd.DataFrame(
        list(study_data.items()),
        columns=["Cardio Intensity", "Energy Improvement Effect Size"]
    )
    st.write(meta.get("chart_title", "Energy improvement relative to control group"))

    chart_spec = {
        "mark": "bar",
        "encoding": {
            "x": {
                "field": "Cardio Intensity",
                "type": "nominal",
                "axis": {"labelAngle": 0}
            },
            "y": {
                "field": "Energy Improvement Effect Size",
                "type": "quantitative"
            }
        },
        "data": {"values": study_df.to_dict(orient="records")}
    }
    st.vega_lite_chart(chart_spec, use_container_width=True)
    st.write("""The Meta-Analysis found a cumulative Cohen's d-value of 0.47 for individuals engaging in moderate-to-high levels of chronic aerobic exercise,
which points to a moderate but statistically significant increase in reported energy for these individuals. The group of low-medium levels of exercise have a
value of 0.31, which is a smaller but still significant positive correlation with higher energy levels when measured against the control group.""")
else:
    st.info("No study data found in JSON. Please add 'study_energy_effects' to data.json.")

#the survey data chart table
st.header("Data Preview")
st.write(f"Here is the raw entries of data collected from my survey")
filtered["date"] = filtered["date"].dt.date
filtered = filtered.reset_index(drop=True)
st.dataframe(filtered, hide_index=True)

# 2 line graph steps vs energy over time DYNAMIC GRAPH #1
st.subheader("Steps vs. Energy Levels")

if not filtered.empty:
    time_df = filtered.sort_values("date")

    fig, ax1 = plt.subplots()
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    fig.autofmt_xdate()

    ax1.plot(time_df["date"], time_df["steps"], label="Steps", linewidth=2, color="blue")
    ax1.set_xlabel("Date")
    ax1.set_ylabel("Steps", color="blue")
    ax1.tick_params(axis='y', labelcolor="blue")
    ax2 = ax1.twinx()
    ax2.plot(time_df["date"], time_df["energy"], label="Energy Level", linewidth=2, color="green")
    ax2.set_ylabel("Energy Level (1–10)", color="green")
    ax2.tick_params(axis='y', labelcolor="green")
    ax2.set_ylim(0, 10)

    lines_1, labels_1 = ax1.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()
    fig.legend(lines_1 + lines_2, labels_1 + labels_2, loc="upper left")

    fig.suptitle("Step Count and Energy Level Data")
    fig.tight_layout()
    st.pyplot(fig)
    
    st.write(
        """This graph displays the data from the survey, and how steps correlate with energy.
Try playing around with the filters on the sidebar to see how different parameters or keywords affect trends (eg. Keyword: "energy drink"."""
    )
else:
    st.info("Add CSV data to view dynamic steps and energy trends over time.")


#Defining energy for the pie charts
def energy_category(e):
    if 0 <= e <= 3:
        return "Low Energy"
    elif 4 <= e <= 6:
        return "Medium Energy"
    elif 7 <= e <= 10:
        return "High Energy"
    else:
        return "Invalid"

# Pie chart of energy level frequency for low exercise range DYNAMIC GRAPH #2

st.subheader("Energy Levels for Low Exercise")

if not filtered.empty:
    low_steps_group = filtered[filtered["steps"] < 6000].copy()

    if low_steps_group.empty:
        st.info("No respondents with fewer than 6000 steps.")
    else:
        low_steps_group["energy_category"] = low_steps_group["energy"].apply(energy_category)
        energy_counts = low_steps_group["energy_category"].value_counts()

        color_mapping = {
            "Low Energy": "blue",
            "Medium Energy": "orange",
            "High Energy": "green"
        }
        colors = [color_mapping.get(cat, "grey") for cat in energy_counts.index]

        fig, ax = plt.subplots()
        ax.pie(energy_counts, labels=energy_counts.index, autopct='%1.1f%%', colors=colors)
        ax.set_title("Energy levels for low exercise (< 6000 steps)")
        st.pyplot(fig)
        plt.clf()
st.write("""This chart shows the frequency of energy levels for days with low ammounts of carido,
defined as under 6000 steps. The higher frequency of "Low" (1-3 on survey) and "Medium" (4-6 on survey) energy levels demonstrate
the correlation between less cardiovascular exercise and less energy."""
)

# Pie chart of energy levels frequency for high exercise entries DYNAMIC GRAPH #3 BECAUSE WHY NOT (and it makes it easier to make my data work with pie charts to do 2)
st.subheader("Energy Levels for High Exercise")

if not filtered.empty:
    high_steps_group = filtered[filtered["steps"] >= 6000].copy()

    if high_steps_group.empty:
        st.info("No respondents with 6000 or more steps.")
    else:
        high_steps_group["energy_category"] = high_steps_group["energy"].apply(energy_category)
        energy_counts_high = high_steps_group["energy_category"].value_counts()

        color_mapping = {
            "Low Energy": "blue",
            "Medium Energy": "orange",
            "High Energy": "green"
        }
        colors = [color_mapping.get(cat, "grey") for cat in energy_counts_high.index]

        fig2, ax2 = plt.subplots()
        ax2.pie(energy_counts_high, labels=energy_counts_high.index, autopct='%1.1f%%', colors=colors)
        ax2.set_title("Energy levels for high exercise (≥ 6000 steps)")
        st.pyplot(fig2)
        plt.clf()
st.write("""This chart shows the frequency of energy levels for days with high ammounts of carido,
defined as 6000 or more steps. Note the frequency of "High" energy levels (7-10 on the survey) compared
to the graph for low cardio. An increase in the frequency of "High" energy demonstrates the correlation between increased cardio and increased energy."""
)

st.markdown(
    """
    <p style="font-size:12px; color:gray; text-align:center; margin-top:30px;">
    Wender, C. L., Manninen, M., & O’Connor, P. J. (2022). 
    <i>The effect of chronic exercise on energy and fatigue states: a systematic review and meta-analysis of randomized trials.</i> 
    Frontiers in Psychology, 13, 907637.
    </p>
    """,
    unsafe_allow_html=True
)
