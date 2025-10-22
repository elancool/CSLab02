import streamlit as st
import pandas as pd
from datetime import date
from pathlib import Path

st.set_page_config(
    page_title="Survey",  
    page_icon="📝",  
)

st.title("Steps vs. Energy Survey")
st.write("Please contribute data to my study on how steps walked in a day correlates to your energy level. Enter values in whole numbers only (except for notes).")

# Survey
with st.form("walk_form"):
    entry_date = st.date_input("Date", value=date.today())
    steps_str = st.text_input("How many steps did you walk today? (Enter a whole number)", value="")
    energy_str = st.text_input("What was your energy level today? (1–10, numbers only)", value="")
    notes = st.text_input("Optional notes (mood, sleep, caffeine, etc.)")
    submitted = st.form_submit_button("Submit")

if submitted:
    if not steps_str.isdigit():
        st.error("Error: Steps must be a whole number. Please enter digits only (no letters or symbols).")
    elif not energy_str.isdigit():
        st.error("Error: Energy must be a whole number between 1 and 10. Please enter digits only.")
    else:
        steps = int(steps_str)
        energy = int(energy_str)
        if not (1 <= energy <= 10):
            st.error("Error: Energy must be between 1 and 10.")
        else:
            row = {
                "date": pd.to_datetime(entry_date).date().isoformat(),
                "steps": steps,
                "energy": energy,
                "notes": notes
            }

            data_path = Path(__file__).resolve().parent.parent / "data.csv"

            try:
                if data_path.exists():
                    df = pd.read_csv(data_path)
                    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
                else:
                    df = pd.DataFrame([row])
                data_path.parent.mkdir(parents=True, exist_ok=True)
                df.to_csv(data_path, index=False)
                st.success("Entry saved successfully!")
                st.write("Latest entries:")
                st.dataframe(df.tail(5))
            except Exception as e:
                st.error(f"Failed to save entry: {e}")
else:
    st.info("Fill the form and click Submit to save your response")
