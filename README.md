# Patient Information Interface

A simple Streamlit application for nursing staff to enter and update patient information before consultations.

## Features

- Look up patients by ID (e.g., P001)
- View and edit basic patient information
- Manage pre-existing conditions via checkboxes
- Add custom conditions not in the common list
- View a list of all patients in the database

## Installation

1. Clone this repository
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Make sure the `.env` file has the correct path to your database:

```
DATABASE_PATH=/path/to/your/database.db
```

## Running the Application

To start the application on port 8502, use either:

```bash
python run.py
```

Or directly with Streamlit:

```bash
streamlit run patient_info.py --server.port=8502
```

This will start the server and open the application in your default web browser at http://localhost:8502.

## Usage

1. Enter a patient ID (e.g., P001) and click "Load Patient Data"
2. If the patient exists, their information will be displayed for editing
3. If the patient doesn't exist, a new record will be created
4. Edit patient details and select pre-existing conditions
5. Click "Save Patient Information" to update the database
6. Use the sidebar checkbox to view a list of all patients in the database