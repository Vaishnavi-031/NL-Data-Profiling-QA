import os
import tempfile
import json
import pytest
from src.retrieval import ProfilerRetriever

@pytest.fixture
def mock_profile_json():
    """Creates a temporary mock profile.json for testing retrieval."""
    mock_data = {
        "table": {
            "n": 100,
            "n_var": 3,
            "n_cells_missing": 10,
            "p_cells_missing": 0.033,
            "n_duplicates": 5,
            "p_duplicates": 0.05
        },
        "variables": {
            "age": {
                "type": "Numeric",
                "n_missing": 2,
                "p_missing": 0.02,
                "n_distinct": 40,
                "mean": 35.5,
                "min": 18.0,
                "max": 80.0
            },
            "name": {
                "type": "Categorical",
                "n_missing": 0,
                "p_missing": 0.0,
                "n_distinct": 95
            },
            "bonus": {
                "type": "Numeric",
                "n_missing": 8,
                "p_missing": 0.08,
                "n_distinct": 30
            }
        },
        "alerts": [
            "age has 2 (2.0%) missing values",
            "bonus has 8 (8.0%) missing values",
            "bonus is highly correlated with salary"
        ]
    }
    
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w", encoding="utf-8") as f:
        json.dump(mock_data, f)
        temp_json_path = f.name
        
    yield temp_json_path
    
    if os.path.exists(temp_json_path):
        os.remove(temp_json_path)

def test_get_table_stats(mock_profile_json):
    retriever = ProfilerRetriever(mock_profile_json)
    stats = retriever.get_table_stats()
    
    assert stats["n_rows"] == 100
    assert stats["n_columns"] == 3
    assert stats["n_duplicates"] == 5
    assert stats["p_duplicates"] == 0.05
    assert stats["n_cells_missing"] == 10

def test_get_columns_summary(mock_profile_json):
    retriever = ProfilerRetriever(mock_profile_json)
    summary = retriever.get_columns_summary()
    
    assert "age" in summary
    assert summary["age"]["type"] == "Numeric"
    assert summary["age"]["missing_count"] == 2
    assert summary["age"]["mean"] == 35.5
    
    assert "name" in summary
    assert summary["name"]["type"] == "Categorical"
    assert summary["name"]["missing_count"] == 0

def test_get_alerts_and_correlations(mock_profile_json):
    retriever = ProfilerRetriever(mock_profile_json)
    alerts = retriever.get_alerts()
    correlations = retriever.get_correlations_summary()
    
    assert len(alerts) == 3
    assert any("age has 2" in a for a in alerts)
    assert len(correlations) == 1
    assert "bonus is highly correlated with salary" in correlations[0]

def test_retrieve_context_missing_values(mock_profile_json):
    retriever = ProfilerRetriever(mock_profile_json)
    
    # Question about missing values
    context = retriever.retrieve_context("Which column has missing values?")
    assert "Missing Values Breakdown per Column" in context
    assert "age': 2 missing values" in context
    assert "bonus': 8 missing values" in context

def test_retrieve_context_duplicates(mock_profile_json):
    retriever = ProfilerRetriever(mock_profile_json)
    
    # Question about duplicate rows
    context = retriever.retrieve_context("Are there duplicate rows?")
    assert "Duplicate Records Information" in context
    assert "Duplicate Rows Count: 5" in context
    assert "Duplicate Rows Percentage: 5.00%" in context

def test_retrieve_context_correlation(mock_profile_json):
    retriever = ProfilerRetriever(mock_profile_json)
    
    # Question about correlations
    context = retriever.retrieve_context("Which variables correlate?")
    assert "Highly Correlated Columns" in context
    assert "bonus is highly correlated with salary" in context
