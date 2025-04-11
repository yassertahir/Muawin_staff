import streamlit as st
import sqlite3
import pandas as pd
import os
from dotenv import load_dotenv
import json
import time
from datetime import datetime

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
     "Diabetes", "Hypertension", "Asthma", "COPD", "Heart Disease", 
            "Stroke", "Cancer", "Arthritis", "Depression", "Anxiety", 
            "Thyroid Disorder", "Kidney Disease", "Liver Disease", "Obesity",
            "Allergies", "Epilepsy"
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

def get_requests(status=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if status:
        query = "SELECT r.*, p.name as patient_name FROM requests r LEFT JOIN patients p ON r.patient_id = p.id WHERE r.status = ?"
        rows = cursor.execute(query, (status,)).fetchall()
    else:
        query = "SELECT r.*, p.name as patient_name FROM requests r LEFT JOIN patients p ON r.patient_id = p.id"
        rows = cursor.execute(query).fetchall()
        
    conn.close()
    return [dict(row) for row in rows]

def close_request(request_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("UPDATE requests SET status = 'closed' WHERE id = ?", (request_id,))
    
    conn.commit()
    conn.close()
    return True

# Initialize session state for auto-refresh
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = time.time()
    st.session_state.refresh_interval = 30  # Refresh every 30 seconds

# App title and logo
st.set_page_config(page_title="Muawin - Patient Information", layout="wide")

# Display logo and title side by side
col1, col2 = st.columns([1, 5])
with col1:
    st.image("Muawin_logo.png", width=100)
with col2:
    st.title("Patient Information")

# Create tabs for patient info and requests
tab1, tab2 = st.tabs(["Patient Information", "Requests Monitor"])

with tab1:
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

with tab2:
    st.subheader("Patient Requests Monitor")
    
    # Auto-refresh mechanism
    current_time = time.time()
    if current_time - st.session_state.last_refresh > st.session_state.refresh_interval:
        st.session_state.last_refresh = current_time
        st.rerun()
    
    # Display time until next refresh
    time_left = int(st.session_state.refresh_interval - (current_time - st.session_state.last_refresh))
    st.caption(f"Auto-refreshing in {time_left} seconds. Last refreshed at {datetime.now().strftime('%H:%M:%S')}")
    
    if st.button("Refresh Now"):
        st.session_state.last_refresh = current_time
        st.rerun()
    
    # Filter options with "open" as the default
    request_status = st.selectbox("Filter by Status", ["All", "open", "in_progress", "closed"], index=1)
    
    # Get requests based on filter
    if request_status == "All":
        requests = get_requests()
    else:
        requests = get_requests(request_status)
    
    # Display requests in expandable sections
    if not requests:
        st.info("No requests found with the selected status.")
    else:
        for req in requests:
            with st.expander(f"Request #{req['id']} - {req['request_type']} - {req['status']}"):
                cols = st.columns(2)
                
                with cols[0]:
                    st.write(f"**Patient:** {req['patient_name']} (ID: {req['patient_id']})")
                    st.write(f"**Type:** {req['request_type']}")
                    st.write(f"**Created:** {req['created_at']}")
                    
                with cols[1]:
                    st.write(f"**Status:** {req['status']}")
                    if req['appointment_date']:
                        st.write(f"**Appointment:** {req['appointment_date']}")
                    st.write(f"**Notes:** {req['notes'] or 'No notes'}")
                
                # Action buttons
                if req['status'] != 'closed':
                    if st.button("Close Request", key=f"close_{req['id']}"):
                        if close_request(req['id']):
                            st.success(f"Request #{req['id']} has been closed.")
                            st.rerun()
                        else:
                            st.error("Error closing the request.")

# Add viewing of all patients
if st.sidebar.checkbox("View All Patients"):
    conn = get_db_connection()
    patients_df = pd.read_sql_query("SELECT id, name, age, gender, language FROM patients", conn)
    conn.close()
    
    st.sidebar.subheader("Patient List")
    st.sidebar.dataframe(patients_df)