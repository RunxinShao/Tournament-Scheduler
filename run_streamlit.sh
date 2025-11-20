#!/bin/bash
# Helper script to run Streamlit app
# Usage: ./run_streamlit.sh

cd "$(dirname "$0")"
python3 -m streamlit run streamlit_app.py

