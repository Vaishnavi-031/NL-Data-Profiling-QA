import os
from src.retrieval import ProfilerRetriever
from src.llm_helper import GeminiHelper
from src.utils import logger

class ProfileAgent:
    """
    Orchestrates the Chat with Data Profiling Reports loop:
    1. Extract relevant context from profile.json
    2. Query LLM with context & question
    3. Validate output JSON structure
    4. Validate and verify citations against the profile contents
    """
    
    def __init__(self, json_path: str, api_key: str = None):
        self.json_path = json_path
        self.retriever = ProfilerRetriever(json_path)
        self.llm = GeminiHelper(api_key)

    def ask(self, question: str) -> dict:
        """
        Processes a user question about the profile report and returns a structured response.
        
        Args:
            question (str): Natural language question.
            
        Returns:
            dict: Structured response with result, reasoning, recommended_action, and citation.
        """
        logger.info(f"Agent received question: '{question}'")
        
        # 1. Retrieve Context
        try:
            context = self.retriever.retrieve_context(question)
            logger.info("Context retrieval complete.")
        except Exception as e:
            logger.error(f"Failed to retrieve context: {str(e)}")
            return {
                "result": "Error retrieving profiling report data.",
                "reasoning": f"Could not read the JSON report. Error: {str(e)}",
                "recommended_action": "Regenerate the profiling report and try again.",
                "citation": "Retrieval Engine"
            }
            
        # 2. Query Gemini
        response = self.llm.query_profile(question, context)
        
        # 3. Validate Response Schema and Citations
        validated_response = self._validate_and_polish_response(response)
        
        return validated_response

    def _validate_and_polish_response(self, response: dict) -> dict:
        """
        Ensures response contains all required fields and validates the citation.
        """
        required_keys = ["result", "reasoning", "recommended_action", "citation"]
        polished = {}
        
        # Ensure all required keys exist, fill with defaults if missing
        for key in required_keys:
            polished[key] = str(response.get(key, "")).strip()
            if not polished[key]:
                polished[key] = f"No {key} provided by the model."
        
        # Citation validation: Check if the citation actually relates to our dataset structure
        citation_text = polished["citation"]
        columns_summary = self.retriever.get_columns_summary()
        alerts = self.retriever.get_alerts()
        table_stats = self.retriever.get_table_stats()
        
        citation_lower = citation_text.lower()
        verified = False
        
        # Check if it cites a specific column name
        for col in columns_summary.keys():
            if col.lower() in citation_lower:
                verified = True
                break
                
        # Check if it cites table stats or alerts
        if not verified:
            for stat_key in ["row", "observation", "column", "variable", "duplicate", "missing"]:
                if stat_key in citation_lower:
                    verified = True
                    break
                    
        # Check if it matches any alert message
        if not verified:
            for alert in alerts:
                if any(word in citation_lower for word in alert.lower().split() if len(word) > 4):
                    verified = True
                    break
                    
        # If not verified and it is not a generic note, add a flag
        if not verified and "retrieval" not in citation_lower and "system" not in citation_lower:
            polished["citation"] = f"[Unverified Citation] {citation_text}"
            logger.warning(f"Citation verification failed for text: '{citation_text}'")
        else:
            logger.info("Citation verification succeeded.")
            
        return polished
