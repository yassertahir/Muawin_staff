import streamlit as st
import sqlite3
import pandas as pd
import os
from dotenv import load_dotenv
import json
import time
from datetime import datetime

# Load environment variables for local development
load_dotenv()

# Database connection - prioritize Streamlit secrets for cloud deployment
try:
    # Try to get DB path from Streamlit secrets (for cloud deployment)
    DB_PATH = st.secrets.get("DATABASE_PATH", "muawin.db")
except (AttributeError, FileNotFoundError):
    # Fall back to environment variables or local path (for local development)
    DB_PATH = os.getenv('DATABASE_PATH', 'muawin.db')

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

# Common symptoms for checkboxes
COMMON_SYMPTOMS = [
    "Fever", "Headache", "Cough", "Sore Throat", "Fatigue", "Nausea",
    "Vomiting", "Diarrhea", "Abdominal Pain", "Chest Pain", "Shortness of Breath",
    "Dizziness", "Rash", "Joint Pain", "Back Pain", "Sweating", "Chills"
]

# Function to get latest prescription for a patient
def get_latest_prescription(patient_id):
    conn = get_db_connection()
    query = """
        SELECT prescription, consultation_date, diagnosis 
        FROM consultations 
        WHERE patient_id = ? 
        ORDER BY consultation_date DESC 
        LIMIT 1
    """
    result = conn.execute(query, (patient_id,)).fetchone()
    conn.close()
    
    if result:
        # Parse prescription from JSON if it's stored as JSON, otherwise return as is
        try:
            prescription = json.loads(result['prescription'])
        except (json.JSONDecodeError, TypeError):
            # If not valid JSON, return the raw prescription text
            prescription = result['prescription']
        
        return {
            'prescription': prescription,
            'date': result['consultation_date'],
            'diagnosis': result['diagnosis']
        }
    
    return None

# Function to format prescription data into a displayable table
def format_prescription_table(prescription_data):
    if isinstance(prescription_data, list):
        # Handle prescription in list format
        formatted_data = []
        for item in prescription_data:
            if isinstance(item, dict):
                formatted_data.append(item)
            else:
                formatted_data.append({"Medication": item})
        
        return pd.DataFrame(formatted_data)
    
    elif isinstance(prescription_data, dict):
        # Handle prescription in dictionary format
        formatted_data = []
        for medication, details in prescription_data.items():
            if isinstance(details, dict):
                entry = {"Medication": medication, **details}
            else:
                entry = {"Medication": medication, "Instructions": details}
            formatted_data.append(entry)
        
        return pd.DataFrame(formatted_data)
    
    else:
        # Handle text-based prescription format with bullet points
        if isinstance(prescription_data, str):
            # Split the prescription into lines
            lines = prescription_data.strip().split('\n')
            
            # Remove the "PRESCRIPTION:" header if present
            if lines and "PRESCRIPTION:" in lines[0]:
                lines = lines[2:]  # Skip header and blank line
                
            formatted_data = []
            
            for line in lines:
                line = line.strip()
                if not line or line == "":
                    continue
                    
                # Remove bullet point if present
                if line.startswith('•') or line.startswith('* ') or line.startswith('- '):
                    line = line[2:].strip()
                elif line.startswith('1.') or line.startswith('2.'):  # Handle numbered lists
                    line = line[line.find('.')+1:].strip()
                    
                # Parse the components based on the typical format
                # Medication - Dosage - Frequency - Duration (Side effects: list of side effects)
                parts = line.split(' - ')
                med_data = {}
                
                if len(parts) >= 1:
                    med_data["Medication"] = parts[0].strip()
                
                if len(parts) >= 2:
                    med_data["Dosage"] = parts[1].strip()
                    
                if len(parts) >= 3:
                    med_data["Frequency"] = parts[2].strip()
                    
                if len(parts) >= 4:
                    # Handle side effects that are in parentheses 
                    duration_parts = parts[3].split('(Side effects:', 1)
                    med_data["Duration"] = duration_parts[0].strip()
                    
                    if len(duration_parts) > 1:
                        side_effects = duration_parts[1].strip()
                        if side_effects.endswith(')'):
                            side_effects = side_effects[:-1]
                        med_data["Side Effects"] = side_effects
                
                formatted_data.append(med_data)
            
            return pd.DataFrame(formatted_data) if formatted_data else pd.DataFrame({"Medication": ["No medications found"]})
        
        # Fallback for other formats
        return pd.DataFrame({"Prescription": [prescription_data]})

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
            SET name = ?, age = ?, gender = ?, pre_conditions = ?, language = ?,
                temperature = ?, blood_pressure = ?, heart_rate = ?, 
                respiratory_rate = ?, oxygen_saturation = ?, symptoms = ?
            WHERE id = ?
        """, (
            patient_data['name'], 
            patient_data['age'], 
            patient_data['gender'],
            patient_data['pre_conditions'],
            patient_data['language'],
            patient_data.get('temperature', ''),
            patient_data.get('blood_pressure', ''),
            patient_data.get('heart_rate', ''),
            patient_data.get('respiratory_rate', ''),
            patient_data.get('oxygen_saturation', ''),
            patient_data.get('symptoms', ''),
            patient_data['id']
        ))
    else:
        # Insert new patient
        cursor.execute("""
            INSERT INTO patients (
                id, name, age, gender, pre_conditions, language,
                temperature, blood_pressure, heart_rate, 
                respiratory_rate, oxygen_saturation, symptoms
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            patient_data['id'], 
            patient_data['name'], 
            patient_data['age'], 
            patient_data['gender'],
            patient_data['pre_conditions'],
            patient_data['language'],
            patient_data.get('temperature', ''),
            patient_data.get('blood_pressure', ''),
            patient_data.get('heart_rate', ''),
            patient_data.get('respiratory_rate', ''),
            patient_data.get('oxygen_saturation', ''),
            patient_data.get('symptoms', '')
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
st.set_page_config(page_title="Patient Information", layout="wide")

# Display title
st.title("Patient Information")

# Create tabs for patient info, medication, and requests
tab1, tab2, tab3 = st.tabs(["Patient Information", "Patient Medication", "Requests Monitor"])

# Patient ID input (outside tabs, so it's shared between Patient Info and Medication tabs)
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

with tab1:
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
            
            # Vitals section
            st.subheader("Vital Signs")
            vital_cols = st.columns(3)
            
            with vital_cols[0]:
                temperature = st.text_input("Temperature (°F)", value="", placeholder="e.g., 98.6")
                heart_rate = st.text_input("Heart Rate (bpm)", value="", placeholder="e.g., 75")
                
            with vital_cols[1]:
                blood_pressure = st.text_input("Blood Pressure (mmHg)", value="", placeholder="e.g., 120/80")
                respiratory_rate = st.text_input("Respiratory Rate (breaths/min)", value="", placeholder="e.g., 16")
                
            with vital_cols[2]:
                oxygen_saturation = st.text_input("Oxygen Saturation (%)", value="", placeholder="e.g., 98")
            
            # Symptoms section
            st.subheader("Symptoms")
            
            # Parse existing symptoms from JSON string or initialize empty list
            try:
                # Convert None to '[]' before parsing
                symptoms_str = patient.get('symptoms', '[]')
                if symptoms_str is None:
                    symptoms_str = '[]'
                existing_symptoms = json.loads(symptoms_str)
            except json.JSONDecodeError:
                existing_symptoms = []
                
            # Checkboxes for common symptoms
            symptom_cols = st.columns(3)
            selected_symptoms = []
            
            for i, symptom in enumerate(COMMON_SYMPTOMS):
                with symptom_cols[i % 3]:
                    if st.checkbox(symptom, value=symptom in existing_symptoms, key=f"symptom_{symptom}"):
                        selected_symptoms.append(symptom)
            
            # Custom symptom input
            st.write("Add custom symptoms (if not listed above):")
            custom_symptoms = st.text_area("Enter symptoms separated by commas", 
                                        value=", ".join([s for s in existing_symptoms if s not in COMMON_SYMPTOMS]),
                                        height=100)
            
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
                
                # Process custom symptoms
                if custom_symptoms.strip():
                    custom_symptom_list = [s.strip() for s in custom_symptoms.split(',') if s.strip()]
                    all_symptoms = selected_symptoms + custom_symptom_list
                else:
                    all_symptoms = selected_symptoms
                
                # Save to database
                updated_patient = {
                    'id': patient['id'],
                    'name': name,
                    'age': age,
                    'gender': gender,
                    'pre_conditions': json.dumps(all_conditions),
                    'language': language,
                    'temperature': temperature,
                    'blood_pressure': blood_pressure,
                    'heart_rate': heart_rate,
                    'respiratory_rate': respiratory_rate,
                    'oxygen_saturation': oxygen_saturation,
                    'symptoms': json.dumps(all_symptoms)
                }
                
                if save_patient_data(updated_patient):
                    st.success("Patient information saved successfully!")
                    st.session_state.current_patient = updated_patient
                else:
                    st.error("Error saving patient information!")

with tab2:
    if 'current_patient' in st.session_state:
        patient = st.session_state.current_patient
        
        # Get and display latest prescription for this patient
        latest_prescription = get_latest_prescription(patient['id'])
        if latest_prescription:
            st.subheader("Latest Prescription")
            
            # Show diagnosis and date
            st.write(f"**Date:** {latest_prescription['date']}")
            st.write(f"**Diagnosis:** {latest_prescription['diagnosis'] or 'Not specified'}")
            
            # Format prescription as a table based on its structure
            prescription_df = format_prescription_table(latest_prescription['prescription'])
            st.table(prescription_df)
            
            # Display inventory simulation section
            st.subheader("Inventory Status")
            
            # Extract medication names based on prescription format
            medications = []
            prescribed_quantities = {}
            
            if isinstance(latest_prescription['prescription'], list):
                # Handle list format
                for item in latest_prescription['prescription']:
                    if isinstance(item, dict) and 'Medication' in item:
                        medications.append(item['Medication'])
                    elif isinstance(item, str):
                        medications.append(item)
            elif isinstance(latest_prescription['prescription'], dict):
                # Handle dictionary format
                medications = list(latest_prescription['prescription'].keys())
            elif isinstance(latest_prescription['prescription'], str):
                # Handle text format - extract medication names from the first part of each line
                lines = latest_prescription['prescription'].strip().split('\n')
                
                # Skip "PRESCRIPTION:" header if present
                if lines and "PRESCRIPTION:" in lines[0]:
                    lines = lines[2:]  # Skip header and blank line
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                        
                    # Remove bullet point or numbering if present
                    if line.startswith('•') or line.startswith('* ') or line.startswith('- '):
                        line = line[2:].strip()
                    elif line[0].isdigit() and line[1:3] in ['. ', ') ']:
                        line = line[3:].strip()
                        
                    # Extract medication name (first part before any ' - ')
                    parts = line.split(' - ')
                    if parts:
                        medication_name = parts[0].strip()
                        medications.append(medication_name)
                        
                        # Try to parse quantity from dosage information (e.g., "500mg" -> 500)
                        if len(parts) >= 2:
                            dosage_part = parts[1].strip()
                            import re
                            # Extract numbers from dosage (e.g. "500mg" -> 500)
                            dosage_numbers = re.findall(r'\d+', dosage_part)
                            if dosage_numbers:
                                try:
                                    dosage_num = int(dosage_numbers[0])
                                    # Extract frequency information
                                    if len(parts) >= 3:
                                        frequency_part = parts[2].lower()
                                        # Calculate units needed based on frequency phrases
                                        units = 1
                                        if "three times" in frequency_part or "3 times" in frequency_part:
                                            units = 3
                                        elif "twice" in frequency_part or "two times" in frequency_part or "2 times" in frequency_part:
                                            units = 2
                                        
                                        # Extract duration information
                                        duration_days = 7  # Default to a week
                                        if len(parts) >= 4:
                                            duration_part = parts[3].lower()
                                            duration_numbers = re.findall(r'\d+', duration_part)
                                            if duration_numbers and "day" in duration_part:
                                                try:
                                                    duration_days = int(duration_numbers[0])
                                                except ValueError:
                                                    pass
                                            elif "week" in duration_part and duration_numbers:
                                                try:
                                                    duration_days = int(duration_numbers[0]) * 7
                                                except ValueError:
                                                    pass
                                        
                                        # Calculate total quantity needed
                                        prescribed_quantities[medication_name] = units * duration_days
                                    else:
                                        prescribed_quantities[medication_name] = 7  # Default to a week's supply
                                except ValueError:
                                    prescribed_quantities[medication_name] = 5  # Default quantity if parsing fails
                            else:
                                prescribed_quantities[medication_name] = 5  # Default quantity
                        else:
                            prescribed_quantities[medication_name] = 5  # Default quantity
            
            # Generate inventory status for each medication
            import random
            inventory_data = []
            
            if medications:
                for med in medications:
                    if med:  # Skip empty medication names
                        available_quantity = random.randint(0, 30)  # Simulate inventory quantity
                        required_quantity = prescribed_quantities.get(med, 5)  # Get required quantity or default to 5
                        status = "In Stock" if available_quantity >= required_quantity else "Low Stock" if available_quantity > 0 else "Out of Stock"
                        
                        inventory_data.append({
                            "Medication": med,
                            "Available Quantity": available_quantity,
                            "Required Quantity": required_quantity,
                            "Status": status
                        })
                
                # Display inventory table
                if inventory_data:
                    inventory_df = pd.DataFrame(inventory_data)
                    st.table(inventory_df)
                    
                    # Alert for low stock items
                    low_stock = [item for item in inventory_data if item['Status'] != "In Stock"]
                    if low_stock:
                        st.warning(f"Warning: {len(low_stock)} medication(s) need to be restocked!")
                else:
                    st.info("No inventory data available.")
            else:
                st.info("No medications found to check inventory status.")
        else:
            st.info("No prescription records found for this patient.")
    else:
        st.info("Please select a patient first by entering a Patient ID above.")

with tab3:
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
    
    # Filter options with "All" as the default (changed from index=1 to index=0)
    request_status = st.selectbox("Filter by Status", ["All", "open", "in_progress", "closed"], index=0)
    
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