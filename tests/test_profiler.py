import os
import tempfile
import pandas as pd
import pytest
from src.profiler import generate_profile_report

def test_generate_profile_report():
    """Test generating profiling reports from a CSV file."""
    # Create a simple temporary CSV file
    data = {
        "col1": [1, 2, 3, 4, 5],
        "col2": ["A", "B", "C", None, "E"],
        "col3": [10.5, 20.5, 30.5, 40.5, 50.5]
    }
    df = pd.DataFrame(data)
    
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
        df.to_csv(f.name, index=False)
        temp_csv_path = f.name
        
    try:
        # Run profiler
        html_path, json_path = generate_profile_report(temp_csv_path, minimal=True)
        
        # Verify output files exist
        assert os.path.exists(html_path), "HTML report was not created"
        assert os.path.exists(json_path), "JSON report was not created"
        
        # Verify JSON file has content
        assert os.path.getsize(json_path) > 0, "JSON report is empty"
        assert os.path.getsize(html_path) > 0, "HTML report is empty"
        
    finally:
        # Clean up temporary CSV file
        if os.path.exists(temp_csv_path):
            os.remove(temp_csv_path)
