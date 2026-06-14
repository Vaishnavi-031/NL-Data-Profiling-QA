import os
import tempfile
import json
import pytest
from unittest.mock import MagicMock, patch
from src.agent import ProfileAgent

@pytest.fixture
def mock_profile_json():
    """Creates a temporary mock profile.json for testing agent logic."""
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
                "n_distinct": 40
            },
            "name": {
                "type": "Categorical",
                "n_missing": 0,
                "p_missing": 0.0,
                "n_distinct": 95
            }
        },
        "alerts": [
            "age has 2 (2.0%) missing values"
        ]
    }
    
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w", encoding="utf-8") as f:
        json.dump(mock_data, f)
        temp_json_path = f.name
        
    yield temp_json_path
    
    if os.path.exists(temp_json_path):
        os.remove(temp_json_path)

@patch("src.llm_helper.GeminiHelper.query_profile")
def test_agent_happy_path(mock_query, mock_profile_json):
    """Test agent returns valid response when LLM returns correct schema and valid citation."""
    mock_query.return_value = {
        "result": "The column 'age' has 2 missing values.",
        "reasoning": "Inspected the variables section in the profiling report.",
        "recommended_action": "Impute missing ages using median or drop rows.",
        "citation": "Column 'age' missing count metric"
    }
    
    agent = ProfileAgent(mock_profile_json, api_key="dummy_key")
    response = agent.ask("Which column has missing values?")
    
    assert response["result"] == "The column 'age' has 2 missing values."
    assert response["reasoning"] == "Inspected the variables section in the profiling report."
    assert response["recommended_action"] == "Impute missing ages using median or drop rows."
    assert response["citation"] == "Column 'age' missing count metric"  # Validated citation (contains 'age')

@patch("src.llm_helper.GeminiHelper.query_profile")
def test_agent_missing_key_recovery(mock_query, mock_profile_json):
    """Test agent handles cases where the LLM response is missing a required key."""
    # Missing 'recommended_action'
    mock_query.return_value = {
        "result": "There are 5 duplicate rows in the dataset.",
        "reasoning": "Duplicate statistics check.",
        "citation": "n_duplicates parameter"
    }
    
    agent = ProfileAgent(mock_profile_json, api_key="dummy_key")
    response = agent.ask("Are there duplicate rows?")
    
    assert response["result"] == "There are 5 duplicate rows in the dataset."
    # Check that missing key is automatically populated with a fallback
    assert "recommended_action" in response
    assert response["recommended_action"] == "No recommended_action provided by the model."
    assert response["citation"] == "n_duplicates parameter"

@patch("src.llm_helper.GeminiHelper.query_profile")
def test_agent_unverified_citation(mock_query, mock_profile_json):
    """Test agent flags citations that do not correspond to any dataset properties or metrics."""
    mock_query.return_value = {
        "result": "There are 100 rows in this dataset.",
        "reasoning": "General metrics analysis.",
        "recommended_action": "No actions needed.",
        "citation": "A guess based on standard headers"  # Non-matching citation
    }
    
    agent = ProfileAgent(mock_profile_json, api_key="dummy_key")
    response = agent.ask("How many rows are in the dataset?")
    
    # Should prefix citation with [Unverified Citation]
    assert response["citation"].startswith("[Unverified Citation]")
    assert "A guess based on standard headers" in response["citation"]
