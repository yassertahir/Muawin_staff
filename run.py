#!/usr/bin/env python3
"""
Launcher script for Muawin Patient Information System
Runs the Streamlit app on port 8502
"""

import os
import sys

if __name__ == "__main__":
    # Run the Streamlit app on port 8502
    os.system(f"streamlit run patient_info.py --server.port=8502")