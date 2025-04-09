import streamlit as st
import sqlite3
import pandas as pd
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Database connection
DB_PATH = os.getenv('DATABASE_PATH', '/home/yasir/Downloads/codes/muawin_MVP/muawin.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Common health conditions for checkboxes
COMMON_CONDITIONS = [
    "Diabetes", "Hypertension", "Asthma", "Heart Disease", 
    "Arthritis", "COPD", "Depression", "Anxiety", 
    "Cancer", "Thyroid Disorder", "Obesity"
]

def load_patient_data(patient_id):
    conn = get_db_connection()
    query = "SELECT * FROM patients WHERE id = ?"
    patient = conn.execute(query, (patient_id,)).fetchone()
    conn.close()
    
    if patient:
        return dict(patient)
    return None

def save_patient_data(patient_data):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if patient exists
    exists = cursor.execute("SELECT 1 FROM patients WHERE id = ?", (patient_data['id'],)).fetchone()
    
    if exists:
        # Update existing patient
        cursor.execute("""
            UPDATE patients 
            SET name = ?, age = ?, gender = ?, pre_conditions = ?, language = ?
            WHERE id = ?
        """, (
            patient_data['name'], 
            patient_data['age'], 
            patient_data['gender'],
            patient_data['pre_conditions'],
            patient_data['language'],
            patient_data['id']
        ))
    else:
        # Insert new patient
        cursor.execute("""
            INSERT INTO patients (id, name, age, gender, pre_conditions, language)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            patient_data['id'], 
            patient_data['name'], 
            patient_data['age'], 
            patient_data['gender'],
            patient_data['pre_conditions'],
            patient_data['language']
        ))
    
    conn.commit()
    conn.close()
    return True

# App title
st.set_page_config(page_title="Muawin - Patient Information", layout="wide")
st.title("Patient Information")

# Patient ID input
col1, col2 = st.columns([3, 1])
with col1:
    patient_id = st.text_input("Enter Patient ID (e.g., P001):")
with col2:
    if st.button("Load Patient Data"):
        if patient_id:
            st.session_state.current_patient = load_patient_data(patient_id)
            if not st.session_state.current_patient:
                st.warning(f"Patient with ID {patient_id} not found. Creating new record.")
                st.session_state.current_patient = {
                    'id': patient_id,
                    'name': '',
                    'age': 0,
                    'gender': '',
                    'pre_conditions': '[]',
                    'language': 'English'
                }
        else:
            st.error("Please enter a Patient ID")

# Main form
if 'current_patient' in st.session_state:
    patient = st.session_state.current_patient
    
    with st.form("patient_form"):
        st.subheader("Patient Information")
        
        # Basic information
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Full Name", value=patient.get('name', ''))
            age = st.number_input("Age", min_value=0, max_value=120, value=int(patient.get('age', 0)))
        
        with col2:
            gender = st.selectbox("Gender", ["Male", "Female", "Other"], 
                                index=["Male", "Female", "Other"].index(patient.get('gender', 'Male')) if patient.get('gender') in ["Male", "Female", "Other"] else 0)
            language = st.selectbox("Preferred Language", ["English", "Urdu", "Punjabi", "Other"], 
                                  index=["English", "Urdu", "Punjabi", "Other"].index(patient.get('language', 'English')) if patient.get('language') in ["English", "Urdu", "Punjabi", "Other"] else 0)
        
        # Pre-existing conditions
        st.subheader("Pre-existing Conditions")
        
        # Parse existing conditions from JSON string or initialize empty list
        try:
            existing_conditions = json.loads(patient.get('pre_conditions', '[]'))
        except json.JSONDecodeError:
            existing_conditions = []
            
        # Checkboxes for common conditions
        condition_cols = st.columns(3)
        selected_conditions = []
        
        for i, condition in enumerate(COMMON_CONDITIONS):
            with condition_cols[i % 3]:
                if st.checkbox(condition, value=condition in existing_conditions):
                    selected_conditions.append(condition)
        
        # Custom condition input
        st.write("Add custom conditions (if not listed above):")
        custom_conditions = st.text_area("Enter conditions separated by commas", 
                                        value=", ".join([c for c in existing_conditions if c not in COMMON_CONDITIONS]),
                                        height=100)
        
        # Save button
        submit = st.form_submit_button("Save Patient Information")
        
        if submit:
            # Process custom conditions
            if custom_conditions.strip():
                custom_list = [c.strip() for c in custom_conditions.split(',') if c.strip()]
                all_conditions = selected_conditions + custom_list
            else:
                all_conditions = selected_conditions
            
            # Save to database
            updated_patient = {
                'id': patient['id'],
                'name': name,
                'age': age,
                'gender': gender,
                'pre_conditions': json.dumps(all_conditions),
                'language': language
            }
            
            if save_patient_data(updated_patient):
                st.success("Patient information saved successfully!")
                st.session_state.current_patient = updated_patient
            else:
                st.error("Error saving patient information!")

# Add viewing of all patients
if st.sidebar.checkbox("View All Patients"):
    conn = get_db_connection()
    patients_df = pd.read_sql_query("SELECT id, name, age, gender, language FROM patients", conn)
    conn.close()
    
    st.sidebar.subheader("Patient List")
    st.sidebar.dataframe(patients_df)